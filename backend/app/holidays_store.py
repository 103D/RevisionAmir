from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from datetime import date


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_HOLIDAYS_PATH = BASE_DIR / "data" / "holidays.json"


class HolidaysStore:
    def __init__(self, holidays_path: str | None = None) -> None:
        if holidays_path:
            self.holidays_path = Path(holidays_path)
        else:
            self.holidays_path = DEFAULT_HOLIDAYS_PATH

        self.holidays_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_exists()

    def _ensure_exists(self) -> None:
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
        with self.holidays_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def write(self, data: dict[str, Any]) -> None:
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