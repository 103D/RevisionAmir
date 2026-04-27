from __future__ import annotations

import json
import os
from datetime import date
from typing import Any


class HolidaysStore:
    def __init__(self) -> None:
        # Проверяем, выполняемся ли мы в среде Vercel
        # Vercel устанавливает VER = '1' и/или VERCEL_ENV
        self.is_vercel = bool(os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'))

        if self.is_vercel:
            # В среде Vercel используем переменные окружения для хранения данных
            self.store_key = "HOLIDAYS_DATA"
            # Инициализируем пустыми данными, если переменная не установлена
            if not os.environ.get(self.store_key):
                os.environ[self.store_key] = json.dumps({"holidays": []}, ensure_ascii=False)
        else:
            # В локальной среде используем файловое хранилище
            from pathlib import Path
            BASE_DIR = Path(__file__).resolve().parent.parent
            self.holidays_path = BASE_DIR / "data" / "holidays.json"
            self.holidays_path.parent.mkdir(parents=True, exist_ok=True)
            self._ensure_exists()

    def _ensure_exists(self) -> None:
        if self.is_vercel:
            return  # На Vercel данные хранятся в env, инициализация выше

        if not self.holidays_path.exists():
            self.write({"holidays": []})
            return

        try:
            current = self.read()
        except (json.JSONDecodeError, OSError):
            self.write({"holidays": []})
            return

        if "holidays" not in current or not isinstance(current["holidays"], list):
            current["holidays"] = []
            self.write(current)

    def read(self) -> dict[str, Any]:
        if self.is_vercel:
            data_str = os.environ.get(self.store_key, "")
            if data_str:
                try:
                    return json.loads(data_str)
                except json.JSONDecodeError:
                    pass
            return {"holidays": []}
        else:
            with self.holidays_path.open("r", encoding="utf-8") as file:
                return json.load(file)

    def write(self, data: dict[str, Any]) -> None:
        if self.is_vercel:
            os.environ[self.store_key] = json.dumps(data, ensure_ascii=False)
        else:
            with self.holidays_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)

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
