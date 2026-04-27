from __future__ import annotations

import json
import os
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

        redis_url = os.environ.get('REDIS_URL') or os.environ.get('UPSTASH_REDIS_REST_URL')
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
            except Exception as e:
                print(f"Warning: Redis holidays connection failed: {e}")
                self.redis_client = None

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
