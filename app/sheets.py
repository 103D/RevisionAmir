from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession

logger = logging.getLogger("revision.sheets")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEETS_API_ROOT = "https://sheets.googleapis.com/v4"


def _format_value(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _row_to_values(item: dict[str, Any]) -> list[str]:
    return [
        _format_value(item.get("id")),
        _format_value(item.get("year")),
        _format_value(item.get("month")),
        _format_value(item.get("project")),
        _format_value(item.get("revision_info")),
        _format_value(item.get("event_date")),
        _format_value(item.get("weekday")),
        _format_value(item.get("inspection_type")),
        _format_value(item.get("status")),
        _format_value(item.get("amount_planned")),
        _format_value(item.get("amount_actual")),
    ]


def _row_from_values(values: list[str]) -> dict[str, Any]:
    padded = values + [""] * (11 - len(values))
    return {
        "id": int(padded[0]) if padded[0] else None,
        "year": int(padded[1]) if padded[1] else None,
        "month": padded[2],
        "project": padded[3],
        "revision_info": padded[4],
        "event_date": padded[5],
        "weekday": padded[6],
        "inspection_type": padded[7],
        "status": padded[8],
        "amount_planned": float(padded[9]) if padded[9] else None,
        "amount_actual": float(padded[10]) if padded[10] else None,
    }


def _load_service_account_info() -> dict[str, Any] | None:
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        return None

    candidate = raw.strip()
    if candidate.startswith("{"):
        return json.loads(candidate)

    path = Path(candidate)
    if path.is_file():
        return json.loads(path.read_text())

    return json.loads(candidate)


def has_google_sheets_config() -> bool:
    return bool(os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID") and _load_service_account_info())


def _build_sheets_client():
    info = _load_service_account_info()
    if not info:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not set")

    client_email = info.get("client_email") or info.get("clientEmail")
    private_key = (info.get("private_key") or info.get("privateKey") or "").replace("\\n", "\n")
    if not client_email or not private_key:
        raise RuntimeError("Service account JSON is missing client_email or private_key")

    credentials = Credentials.from_service_account_info(
        {**info, "private_key": private_key}, scopes=SCOPES
    )
    return AuthorizedSession(credentials)


def push_rows_to_sheet(rows: list[dict[str, Any]]) -> dict[str, Any]:
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Schedule")
    if not spreadsheet_id:
        raise RuntimeError("GOOGLE_SHEETS_SPREADSHEET_ID is not set")

    logger.info("Pushing %d rows to sheet '%s' (id=%s)", len(rows), sheet_name, spreadsheet_id[:8])
    sheets = _build_sheets_client()
    values = [[
        "ID",
        "Год",
        "Месяц",
        "Объект",
        "Ревизия",
        "Дата",
        "День недели",
        "Тип",
        "Статус",
        "План",
        "Факт",
    ]]
    values.extend(_row_to_values(item) for item in rows)

    clear_url = f"{SHEETS_API_ROOT}/spreadsheets/{spreadsheet_id}/values/{sheet_name}!A:K:clear"
    update_url = f"{SHEETS_API_ROOT}/spreadsheets/{spreadsheet_id}/values/{sheet_name}!A1"

    clear_response = sheets.post(clear_url)
    clear_response.raise_for_status()
    logger.debug("Sheet cleared successfully")

    update_response = sheets.put(
        update_url,
        params={"valueInputOption": "RAW"},
        json={"values": values},
    )
    update_response.raise_for_status()
    logger.info("Sheet updated with %d rows", len(rows))

    return {"rows_written": len(rows)}


def read_rows_from_sheet() -> list[dict[str, Any]]:
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Schedule")
    if not spreadsheet_id:
        raise RuntimeError("GOOGLE_SHEETS_SPREADSHEET_ID is not set")

    logger.info("Reading from sheet '%s' (id=%s)", sheet_name, spreadsheet_id[:8])
    sheets = _build_sheets_client()
    get_url = f"{SHEETS_API_ROOT}/spreadsheets/{spreadsheet_id}/values/{sheet_name}!A2:K"
    response = sheets.get(get_url)
    response.raise_for_status()
    data = response.json()

    values = data.get("values", [])
    rows = [
        row for row in (
            _row_from_values(values_row) for values_row in values
        )
        if row["year"] and row["month"] and row["project"]
    ]
    logger.info("Read %d rows from sheet", len(rows))
    return rows
