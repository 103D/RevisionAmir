from __future__ import annotations

import threading
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException

try:
    from .schemas import FilialCreate, FilialUpdate, NextRevisionUpdate, RevisionDatesUpdate
    from .redis_store import RedisStore
    from .redis_holidays_store import RedisHolidaysStore
except ImportError:
    from schemas import FilialCreate, FilialUpdate, NextRevisionUpdate, RevisionDatesUpdate
    from redis_store import RedisStore
    from redis_holidays_store import RedisHolidaysStore


class RevisionService:
    EXCLUDED_WEEKDAYS = {4, 5, 6}
    GENERATION_HORIZON_MONTHS = 24
    ALLOWED_STATUSES = {"planned", "postponed"}

    def __init__(self, store: RedisStore) -> None:
        self.store = store
        self.holidays_store = RedisHolidaysStore()
        self._lock = threading.RLock()

    @staticmethod
    def _to_date(value: str) -> date:
        return date.fromisoformat(value)

    @staticmethod
    def _to_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value)

    @staticmethod
    def _dates_to_iso(dates: list[date]) -> list[str]:
        unique_dates = sorted(set(dates))
        return [d.isoformat() for d in unique_dates]

    def _normalize_status(self, value: str | None) -> str:
        if value in self.ALLOWED_STATUSES:
            return value
        return "planned"

    def _add_months(self, value: date, months: int = 3) -> date:
        year = value.year + (value.month - 1 + months) // 12
        month = (value.month - 1 + months) % 12 + 1
        day = min(value.day, monthrange(year, month)[1])
        return date(year, month, day)

    def _collect_holidays(self, data: dict | None = None) -> set[date]:
        return self.holidays_store.get_holidays_as_dates()

    def _collect_occupied_dates(self, filials: list[dict], exclude_id: str | None = None) -> set[date]:
        occupied_dates: set[date] = set()
        for filial in filials:
            if exclude_id is not None and filial.get("id") == exclude_id:
                continue

            first_revision_date = filial.get("first_revision_date")
            if isinstance(first_revision_date, str):
                occupied_dates.add(self._to_date(first_revision_date))

            for item in filial.get("revision_dates", []):
                if isinstance(item, str):
                    occupied_dates.add(self._to_date(item))

        return occupied_dates

    def _is_allowed_date(self, candidate: date, occupied_dates: set[date], holidays: set[date]) -> bool:
        if candidate.weekday() in self.EXCLUDED_WEEKDAYS:
            return False

        if candidate in holidays:
            return False

        return all(abs((candidate - occupied_date).days) >= 2 for occupied_date in occupied_dates)

    def _shift_to_allowed_date(
        self,
        candidate: date,
        occupied_dates: set[date],
        holidays: set[date],
        direction: int,
    ) -> date:
        step = timedelta(days=1 if direction >= 0 else -1)

        for _ in range(120):
            if self._is_allowed_date(candidate, occupied_dates, holidays):
                return candidate
            candidate += step

        return candidate

    def _calculate_previous_next(
        self,
        first_revision_date: date,
        revision_dates: list[date],
        occupied_dates: set[date],
        holidays: set[date],
    ) -> tuple[date | None, date | None]:
        all_dates = sorted(set([first_revision_date, *revision_dates]))
        today = date.today()

        previous_dates = [revision_date for revision_date in all_dates if revision_date <= today]
        future_dates = [revision_date for revision_date in all_dates if revision_date > today]

        previous = previous_dates[-1] if previous_dates else None

        if future_dates:
            next_date = future_dates[0]
        else:
            next_date = self._generate_next_date(first_revision_date, occupied_dates, holidays, today)

        return previous, next_date

    def _generate_next_date(
        self,
        first_revision_date: date,
        occupied_dates: set[date],
        holidays: set[date],
        today: date,
    ) -> date:
        candidate = self._shift_to_allowed_date(first_revision_date, occupied_dates, holidays, direction=1)

        if candidate > today:
            return candidate

        for _ in range(24):
            candidate = self._add_months(candidate, 3)
            candidate = self._shift_to_allowed_date(candidate, occupied_dates, holidays, direction=1)

            if candidate > today:
                return candidate

        return candidate

    def _generate_revision_dates(
        self,
        first_revision_date: date,
        occupied_dates: set[date],
        holidays: set[date],
        existing_dates: list[date] | None = None,
    ) -> list[date]:
        generated_dates = sorted(set(existing_dates or []))
        last_date = generated_dates[-1] if generated_dates else self._shift_to_allowed_date(
            first_revision_date,
            occupied_dates,
            holidays,
direction=1,
        )

        horizon_end = self._add_months(first_revision_date, self.GENERATION_HORIZON_MONTHS)

        for _ in range(24):
            next_candidate = self._add_months(last_date, 3)
            if next_candidate > horizon_end:
                break

            next_candidate = self._shift_to_allowed_date(next_candidate, occupied_dates, holidays, direction=1)
            if next_candidate <= last_date:
                break

            generated_dates.append(next_candidate)
            last_date = next_candidate

        return self._dates_to_iso(generated_dates)

    def _generate_following_dates_from_next(
        self,
        next_revision_date: date,
        occupied_dates: set[date],
        holidays: set[date],
    ) -> list[str]:
        following_dates: list[date] = []
        horizon_end = self._add_months(next_revision_date, self.GENERATION_HORIZON_MONTHS)

        for i in range(24):
            months_offset = (i + 1) * 3
            candidate = self._add_months(next_revision_date, months_offset)
            if candidate > horizon_end:
                break

            candidate = self._shift_to_allowed_date(candidate, occupied_dates, holidays, direction=1)
            
            if following_dates and candidate <= following_dates[-1]:
                break

            following_dates.append(candidate)

        return self._dates_to_iso(following_dates)

    def _sync_revision_statuses(
        self,
        record: dict,
        next_revision_date: date | None,
        revision_dates: list[date],
        next_status: str | None = None,
    ) -> None:
        existing_statuses = record.get("revision_statuses", {}) if isinstance(record.get("revision_statuses"), dict) else {}
        statuses: dict[str, str] = {}

        if next_revision_date is not None:
            next_iso = next_revision_date.isoformat()
            statuses[next_iso] = self._normalize_status(next_status or existing_statuses.get(next_iso))
            record["next_revision_status"] = statuses[next_iso]
        else:
            record["next_revision_status"] = "planned"

        for revision_date in revision_dates:
            revision_iso = revision_date.isoformat()
            statuses[revision_iso] = self._normalize_status(existing_statuses.get(revision_iso))

        record["revision_statuses"] = statuses

    def _format_record(self, raw_record: dict) -> dict:
        revision_statuses = raw_record.get("revision_statuses", {})
        if not isinstance(revision_statuses, dict):
            revision_statuses = {}

        revision_shortages = raw_record.get("revision_shortages", {})
        if not isinstance(revision_shortages, dict):
            revision_shortages = {}

        previous_date = raw_record.get("previous_revision_date")
        next_date = raw_record.get("next_revision_date")
        shortage = float(raw_record.get("shortage", 0) or 0)
        if previous_date and str(previous_date) in revision_shortages:
            shortage = float(revision_shortages[str(previous_date)])
        elif next_date and str(next_date) in revision_shortages:
            shortage = float(revision_shortages[str(next_date)])

        return {
            "id": raw_record["id"],
            "name": raw_record["name"],
            "first_revision_date": self._to_date(raw_record["first_revision_date"]),
            "previous_revision_date": self._to_date(previous_date) if previous_date else None,
            "next_revision_date": self._to_date(next_date) if next_date else None,
            "revision_dates": [self._to_date(item) for item in raw_record.get("revision_dates", [])],
            "next_revision_status": self._normalize_status(raw_record.get("next_revision_status")),
            "shortage": shortage,
            "revision_shortages": {str(key): float(value) for key, value in revision_shortages.items()},
            "revision_statuses": {str(key): self._normalize_status(value) for key, value in revision_statuses.items()},
            "created_at": self._to_datetime(raw_record["created_at"]),
            "updated_at": self._to_datetime(raw_record["updated_at"]),
        }

    def _persist_computed_dates(self, record: dict, filials: list[dict], data: dict) -> dict:
        """
        Compute previous_revision_date and next_revision_date based on revision_dates.
        Does NOT modify stored fields; returns computed values for API response.
        """
        # Получаем даты
        first_revision_date = self._to_date(record["first_revision_date"])
        revision_dates = [self._to_date(item) for item in record.get("revision_dates", [])]
        all_dates = set(revision_dates)
        if first_revision_date:
            all_dates.add(first_revision_date)
        all_dates = sorted(all_dates)

        today = date.today()

        past_dates = [d for d in all_dates if d <= today]
        future_dates = [d for d in all_dates if d > today]

        if past_dates:
            previous = past_dates[-1]
        else:
            # Нет прошедших ревизий, проверяем кратность 3 месяцев от первой ревизии
            first = first_revision_date
            months_diff = (today.year - first.year) * 12 + (today.month - first.month)
            if months_diff % 3 == 0 and today >= first:
                previous = first
            else:
                previous = None

        next_date = future_dates[0] if future_dates else None

        occupied_dates = self._collect_occupied_dates(filials, exclude_id=record.get("id"))
        holidays = self._collect_holidays(data)

        # Если нет будущей даты — генерируем новую
        generated_new_next = False
        if next_date is None:
            base_date = all_dates[-1] if all_dates else first_revision_date
            next_date = self._generate_next_date(base_date, occupied_dates, holidays, today)
            if next_date not in all_dates:
                all_dates.append(next_date)
                all_dates = sorted(set(all_dates))
                generated_new_next = True

        # Гарантируем минимум 6 будущих дат после next_date
        future_after_next = [d for d in all_dates if d > next_date]
        if len(future_after_next) < 6:
            additional = self._generate_following_dates_from_next(next_date, occupied_dates, holidays)
            for d_str in additional:
                d = self._to_date(d_str)
                if d not in all_dates:
                    all_dates.append(d)
            all_dates = sorted(set(all_dates))

        # Не модифицируем record! Только вычисляем
        # Синхронизируем статусы (для API)
        self._sync_revision_statuses(
            {**record},  # копия, чтобы не менять оригинал
            next_date,
            all_dates,
        )

        return {
            "previous_revision_date": previous.isoformat() if previous else None,
            "next_revision_date": next_date.isoformat() if next_date else None,
        }

    def _find_index(self, filials: list[dict], filial_id: str) -> int:
        for index, filial in enumerate(filials):
            if filial["id"] == filial_id:
                return index
        raise HTTPException(status_code=404, detail="Filial not found")

    def list_filials(self) -> list[dict]:
        with self._lock:
            data = self.store.read()
            filials = data.get("filials", [])
            result = []
            for filial in filials:
                computed = self._persist_computed_dates(filial, filials, data)
                filial_with_computed = {**filial, **computed}
                result.append(self._format_record(filial_with_computed))
            return result

    def get_filial(self, filial_id: str) -> dict:
        with self._lock:
            data = self.store.read()
            filials = data.get("filials", [])
            index = self._find_index(filials, filial_id)
            filial = filials[index]
            computed = self._persist_computed_dates(filial, filials, data)
            filial_with_computed = {**filial, **computed}
            return self._format_record(filial_with_computed)

    def create_filial(self, payload: FilialCreate) -> dict:
        with self._lock:
            data = self.store.read()
            filials = data.setdefault("filials", [])

            now = datetime.now(timezone.utc).isoformat()
            record = {
                "id": str(uuid4()),
                "name": payload.name,
                "first_revision_date": payload.first_revision_date.isoformat(),
                "shortage": float(payload.shortage),
                "revision_dates": self._dates_to_iso(payload.revision_dates),
                "revision_statuses": {},
                "revision_shortages": {},
                "created_at": now,
                "updated_at": now,
            }
            # previous_revision_date и next_revision_date НЕ сохраняем!
            filials.append(record)
            self.store.write(data)
            # Для API-ответа вычисляем computed
            computed = self._persist_computed_dates(record, filials, data)
            return self._format_record({**record, **computed})

    def update_filial(self, filial_id: str, payload: FilialUpdate) -> dict:
        with self._lock:
            data = self.store.read()
            filials = data.get("filials", [])
            index = self._find_index(filials, filial_id)
            record = filials[index]

            if payload.name is not None:
                record["name"] = payload.name
            if payload.first_revision_date is not None:
                record["first_revision_date"] = payload.first_revision_date.isoformat()
            record["updated_at"] = datetime.now(timezone.utc).isoformat()
            # previous_revision_date и next_revision_date НЕ сохраняем!
            filials[index] = record
            self.store.write(data)
            computed = self._persist_computed_dates(record, filials, data)
            return self._format_record({**record, **computed})

    def delete_filial(self, filial_id: str) -> None:
        with self._lock:
            data = self.store.read()
            filials = data.get("filials", [])
            index = self._find_index(filials, filial_id)
            filials.pop(index)
            self.store.write(data)

    def update_revision_dates(self, filial_id: str, payload: RevisionDatesUpdate) -> dict:
        with self._lock:
            data = self.store.read()
            filials = data.get("filials", [])
            index = self._find_index(filials, filial_id)
            record = filials[index]

            # first_revision_date remains immutable here; only subsequent dates are editable.
            record["revision_dates"] = self._dates_to_iso(payload.revision_dates)
            record["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._persist_computed_dates(record, filials, data)

            filials[index] = record
            self.store.write(data)

            return self._format_record(record)

    def update_next_revision(self, filial_id: str, payload: NextRevisionUpdate) -> dict:
        with self._lock:
            data = self.store.read()
            filials = data.get("filials", [])
            index = self._find_index(filials, filial_id)
            record = filials[index]
            requested_next_iso = payload.next_revision_date.isoformat()

            occupied_dates = self._collect_occupied_dates(filials, exclude_id=record.get("id"))
            holidays = self._collect_holidays(data)

            # Сдвигаем дату на разрешённую
            next_revision_date = self._shift_to_allowed_date(
                payload.next_revision_date,
                occupied_dates,
                holidays,
                direction=1,
            )

            # Обновляем revision_dates (добавляем дату, если её нет)
            revision_dates = [self._to_date(item) for item in record.get("revision_dates", [])]
            if next_revision_date not in revision_dates:
                revision_dates.append(next_revision_date)
            revision_dates = sorted(set(revision_dates))
            record["revision_dates"] = self._dates_to_iso(revision_dates)

            revision_statuses = record.setdefault("revision_statuses", {})
            revision_shortages = record.setdefault("revision_shortages", {})
            today = date.today()

            # Валидация: статус "planned" нельзя установить на прошедшую дату
            if next_revision_date <= today:
                if payload.status == "planned":
                    raise HTTPException(
                        status_code=400,
                        detail="Невозможно установить статус 'planned' на прошедшую дату. Используйте статус 'postponed' или укажите будущую дату."
                    )
                revision_statuses[next_revision_date.isoformat()] = "done"
                revision_shortages[next_revision_date.isoformat()] = float(record.get("shortage", 0) or 0)
            else:
                auto_status = payload.status if hasattr(payload, "status") and payload.status in self.ALLOWED_STATUSES else "planned"
                revision_statuses[next_revision_date.isoformat()] = auto_status

            record["updated_at"] = datetime.now(timezone.utc).isoformat()
            filials[index] = record
            self.store.write(data)

            # previous_revision_date и next_revision_date НЕ сохраняем!
            computed = self._persist_computed_dates(record, filials, data)
            return self._format_record({**record, **computed})
