from __future__ import annotations

import json
import os
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

        redis_url = os.environ.get('REDIS_URL') or os.environ.get('UPSTASH_REDIS_REST_URL')
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
            except Exception as e:
                print(f"Warning: Redis connection failed: {e}")
                self.redis_client = None

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
