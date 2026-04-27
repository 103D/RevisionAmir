from __future__ import annotations

import json
import os
import time
from datetime import date
from typing import Any

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RedisHolidaysStore:
    """Holidays storage: Redis priority, fallback to file/env"""

    def __init__(self) -> None:
        self.is_vercel = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'))
        self.redis_client: Any | None = None
        self._fallback_store: Any | None = None

        redis_url = os.environ.get('REDIS_URL')
        if not redis_url:
            return

        if REDIS_AVAILABLE:
            try:
                connect_kwargs = {"decode_responses": True}
                if redis_url.startswith('rediss://'):
                    connect_kwargs["ssl_cert_reqs"] = None

                for attempt in range(3):
                    try:
                        self.redis_client = redis.from_url(redis_url, **connect_kwargs)
                        self.redis_client.ping()
                        print(f"✓ Connected to Redis (holidays): {redis_url[:40]}...")
                        self._migrate_if_needed()
                        break
                    except Exception as e:
                        if attempt < 2:
                            print(f"Retrying Redis holidays connection ({attempt + 1}/3): {e}")
                            time.sleep(1)
                        else:
                            raise e
            except Exception as e:
                print(f"Warning: Redis holidays connection failed: {e}")
                self.redis_client = None
        else:
            print("Warning: redis-py not installed")

    def _migrate_if_needed(self) -> None:
        """Если в Redis нет данных или ключ неверного типа, загружаем из локальных файлов"""
        if not self.redis_client:
            return
        try:
            key_type = self.redis_client.type("holidays:data")
            if key_type == "string":
                return
            elif key_type != "none":
                print(f"Warning: holidays:data has wrong type '{key_type}', replacing")
                self.redis_client.delete("holidays:data")
        except Exception as e:
            print(f"Warning: Could not check holidays:data type: {e}")

        try:
            from pathlib import Path
            BASE_DIR = Path(__file__).resolve().parent.parent
            local_file = BASE_DIR / "data" / "holidays.json"
            if local_file.exists():
                with local_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                self.redis_client.set("holidays:data", json.dumps(data, ensure_ascii=False))
                print(f"✓ Migrated holidays.json to Redis ({len(data.get('holidays', []))} holidays)")
        except Exception as e:
            print(f"Warning: Could not migrate holidays.json: {e}")

    def _get_fallback(self):
        if self._fallback_store is None:
            if self.is_vercel:
                self._fallback_store = EnvVarHolidaysStore()
            else:
                try:
                    from app.holidays_store import HolidaysStore as FileHolidaysStore
                except ImportError:
                    from holidays_store import HolidaysStore as FileHolidaysStore
                self._fallback_store = FileHolidaysStore()
        return self._fallback_store

    def read(self) -> dict[str, Any]:
        if self.redis_client:
            try:
                data_str = self.redis_client.get("holidays:data")
                if data_str:
                    return json.loads(data_str)
                return {"holidays": []}
            except Exception as e:
                print(f"Redis holidays read error: {e}")
                return self._get_fallback().read()
        return self._get_fallback().read()

    def write(self, data: dict[str, Any]) -> None:
        dumped = json.dumps(data, ensure_ascii=False, indent=2)
        if self.redis_client:
            try:
                self.redis_client.set("holidays:data", dumped)
                return
            except Exception as e:
                print(f"Redis holidays write error: {e}")
                pass
        self._get_fallback().write(data)

    def get_all_holidays(self) -> list[dict[str, Any]]:
        data = self.read()
        return data.get("holidays", [])

    def get_holidays_as_dates(self) -> set[date]:
        holidays: set[date] = set()
        for item in self.get_all_holidays():
            if isinstance(item, dict):
                raw_date = item.get("date")
                if isinstance(raw_date, str):
                    holidays.add(date.fromisoformat(raw_date))
        return holidays

    def add_holiday(self, holiday_data: dict[str, Any]) -> None:
        data = self.read()
        holidays = data.setdefault("holidays", [])
        holidays.append(holiday_data)
        self.write(data)

    def update_holiday(self, holiday_date: str, holiday_data: dict[str, Any]) -> bool:
        data = self.read()
        holidays = data.get("holidays", [])
        for holiday in holidays:
            if holiday.get("date") == holiday_date:
                holiday.update(holiday_data)
                self.write(data)
                return True
        return False

    def delete_holiday(self, holiday_date: str) -> bool:
        data = self.read()
        holidays = data.get("holidays", [])
        for i, holiday in enumerate(holidays):
            if holiday.get("date") == holiday_date:
                holidays.pop(i)
                self.write(data)
                return True
        return False


class EnvVarHolidaysStore:
    """Simple env-var holidays store (Vercel fallback without Redis)"""

    def __init__(self) -> None:
        self.key = "HOLIDAYS_DATA"
        if not os.environ.get(self.key):
            os.environ[self.key] = json.dumps({"holidays": []}, ensure_ascii=False)

    def read(self) -> dict[str, Any]:
        data_str = os.environ.get(self.key, "")
        if data_str:
            try:
                return json.loads(data_str)
            except json.JSONDecodeError:
                pass
        return {"holidays": []}

    def write(self, data: dict[str, Any]) -> None:
        os.environ[self.key] = json.dumps(data, ensure_ascii=False)

    def get_all_holidays(self) -> list[dict[str, Any]]:
        return self.read().get("holidays", [])

    def get_holidays_as_dates(self) -> set[date]:
        holidays: set[date] = set()
        for item in self.get_all_holidays():
            if isinstance(item, dict):
                raw_date = item.get("date")
                if isinstance(raw_date, str):
                    holidays.add(date.fromisoformat(raw_date))
        return holidays

    def add_holiday(self, holiday_data: dict[str, Any]) -> None:
        data = self.read()
        data.setdefault("holidays", []).append(holiday_data)
        self.write(data)

    def update_holiday(self, holiday_date: str, holiday_data: dict[str, Any]) -> bool:
        data = self.read()
        holidays = data.get("holidays", [])
        for holiday in holidays:
            if holiday.get("date") == holiday_date:
                holiday.update(holiday_data)
                self.write(data)
                return True
        return False

    def delete_holiday(self, holiday_date: str) -> bool:
        data = self.read()
        holidays = data.get("holidays", [])
        for i, holiday in enumerate(holidays):
            if holiday.get("date") == holiday_date:
                holidays.pop(i)
                self.write(data)
                return True
        return False
