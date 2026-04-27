from __future__ import annotations

import json
import os
import time
from typing import Any

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisStore:
    """
    JSON-совместимое хранилище на основе Redis.
    Приоритет: Redis > Fallback (env vars / JSON файлы).
    """

    def __init__(self) -> None:
        self.is_vercel = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'))
        self.redis_client: Any | None = None
        self._fallback_store: Any | None = None

        redis_url = os.environ.get('REDIS_URL')
        if not redis_url:
            # Fallback: no Redis configured
            return

        if REDIS_AVAILABLE:
            try:
                # Upstash uses rediss:// (SSL). For SSL connections, disable cert verification
                # because Upstash uses self-signed certificates.
                connect_kwargs = {"decode_responses": True}
                if redis_url.startswith('rediss://'):
                    connect_kwargs["ssl_cert_reqs"] = None

                # Retry logic
                for attempt in range(3):
                    try:
                        self.redis_client = redis.from_url(redis_url, **connect_kwargs)
                        self.redis_client.ping()
                        print(f"✓ Connected to Redis: {redis_url[:40]}...")
                        self._migrate_if_needed()
                        break
                    except Exception as e:
                        if attempt < 2:
                            print(f"Retrying Redis connection ({attempt + 1}/3): {e}")
                            time.sleep(1)
                        else:
                            raise e
            except Exception as e:
                print(f"Warning: Redis connection failed: {e}")
                self.redis_client = None
        else:
            print("Warning: redis-py not installed, install with: pip install redis")

    def _migrate_if_needed(self) -> None:
        """Если в Redis нет данных или ключ неверного типа, загружаем из локальных файлов"""
        if not self.redis_client:
            return
        try:
            key_type = self.redis_client.type("store:data")
            if key_type == "string":
                # Ключ уже существует и это строка — ничего не делаем
                return
            elif key_type != "none":
                # Ключ существует, но не строка — удаляем
                print(f"Warning: store:data has wrong type '{key_type}', replacing")
                self.redis_client.delete("store:data")
        except Exception as e:
            print(f"Warning: Could not check store:data type: {e}")

        try:
            from pathlib import Path
            BASE_DIR = Path(__file__).resolve().parent.parent
            local_file = BASE_DIR / "data" / "store.json"
            if local_file.exists():
                with local_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                self.redis_client.set("store:data", json.dumps(data, ensure_ascii=False))
                print(f"✓ Migrated store.json to Redis ({len(data.get('filials', []))} filials)")
        except Exception as e:
            print(f"Warning: Could not migrate store.json: {e}")

    def _get_fallback(self):
        if self._fallback_store is None:
            if self.is_vercel:
                self._fallback_store = EnvVarStore()
            else:
                try:
                    from app.store import JsonStore as FileStore
                except ImportError:
                    from store import JsonStore as FileStore
                self._fallback_store = FileStore()
        return self._fallback_store

    def read(self) -> dict[str, Any]:
        if self.redis_client:
            try:
                data_str = self.redis_client.get("store:data")
                if data_str:
                    return json.loads(data_str)
                # Ключ отсутствует — пустая структура
                return {"filials": []}
            except Exception as e:
                print(f"Redis read error: {e}")
                # При ошибке Redis — fallback
                return self._get_fallback().read()
        # Без Redis — fallback
        return self._get_fallback().read()

    def write(self, data: dict[str, Any]) -> None:
        dumped = json.dumps(data, ensure_ascii=False, indent=2)
        if self.redis_client:
            try:
                self.redis_client.set("store:data", dumped)
                return
            except Exception as e:
                print(f"Redis write error: {e}")
                # При ошибке — fallback
                pass
        self._get_fallback().write(data)


class EnvVarStore:
    """In-memory storage using environment variables (Vercel fallback)"""

    def __init__(self) -> None:
        self.key = "STORE_DATA"
        if not os.environ.get(self.key):
            os.environ[self.key] = json.dumps({"filials": []}, ensure_ascii=False)

    def read(self) -> dict[str, Any]:
        data_str = os.environ.get(self.key, "")
        if data_str:
            try:
                return json.loads(data_str)
            except json.JSONDecodeError:
                pass
        return {"filials": []}

    def write(self, data: dict[str, Any]) -> None:
        os.environ[self.key] = json.dumps(data, ensure_ascii=False)
