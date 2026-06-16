from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .db import (
    count_schedule_items,
    create_schedule_item,
    delete_schedule_item,
    get_audit_logs,
    get_dashboard_stats,
    get_schedule_item,
    list_schedule_items,
    open_database,
    replace_all_schedule_items,
    search_schedule_items,
    update_schedule_item,
)
from .export import generate_excel
from .sheets import has_google_sheets_config, push_rows_to_sheet, read_rows_from_sheet


# ---------- logging ----------
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("revision")

# ---------- paths ----------
BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "schedule.db"))
PORT = int(os.getenv("PORT", "8000"))

# ---------- app ----------
app = FastAPI(title="Revision Amir Schedule App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")
database = open_database(DATABASE_PATH)

logger.info("App started, database=%s, port=%d", DATABASE_PATH, PORT)


# ---------- Pydantic schemas ----------
class ScheduleItemInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    year: int = Field(ge=2000, le=2100)
    month: str = Field(min_length=2, max_length=20)
    project: str = Field(min_length=1, max_length=200)
    revision_info: str = Field(alias="revisionInfo", min_length=1, max_length=200)
    event_date: str = Field(alias="eventDate", min_length=8, max_length=12)
    weekday: str = Field(min_length=2, max_length=20)
    inspection_type: str = Field(alias="inspectionType", min_length=2, max_length=100)
    status: str = Field(min_length=2, max_length=50)
    amount_planned: float | None = Field(default=None, alias="amountPlanned", ge=0)
    amount_actual: float | None = Field(default=None, alias="amountActual", ge=0)


def _item_payload(item: ScheduleItemInput) -> dict[str, object]:
    return item.model_dump(by_alias=False, mode="json")


# ---------- middleware: request logging ----------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("%s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("%s %s → %s", request.method, request.url.path, response.status_code)
    return response


# ---------- exception handlers ----------
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": [
                    {"field": ".".join(e["loc"]), "message": e["msg"]}
                    for e in exc.errors()
                ],
            }
        },
    )


# ---------- routes ----------
@app.get("/")
def root() -> FileResponse:
    return FileResponse(PUBLIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/api/config")
def config() -> dict[str, bool]:
    sheets_configured = has_google_sheets_config()
    logger.debug("sheets configured=%s", sheets_configured)
    return {"sheetsConfigured": sheets_configured}


@app.get("/api/items")
def items(
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    size: int = Query(default=25, ge=1, le=200, description="Размер страницы"),
) -> dict[str, object]:
    offset = (page - 1) * size
    total = count_schedule_items(database)
    all_items = list_schedule_items(database, limit=size, offset=offset)
    logger.debug("GET /api/items page=%d size=%d → %d rows (total=%d)", page, size, len(all_items), total)
    return {"items": all_items, "total": total, "page": page, "size": size}


@app.post("/api/items", status_code=201)
def add_item(item: ScheduleItemInput) -> dict[str, dict[str, object]]:
    logger.info("POST /api/items project=%s", item.project)
    created = create_schedule_item(database, _item_payload(item))
    logger.info("Created item id=%s", created.get("id"))
    return {"item": created}


@app.put("/api/items/{item_id}")
def edit_item(item_id: int, item: ScheduleItemInput) -> dict[str, dict[str, object]]:
    logger.info("PUT /api/items/%s project=%s", item_id, item.project)
    existing = get_schedule_item(database, item_id)
    if existing is None:
        logger.warning("PUT /api/items/%s → 404 not found", item_id)
        raise HTTPException(status_code=404, detail="Item not found")
    updated = update_schedule_item(database, item_id, _item_payload(item))
    logger.info("Updated item id=%s", item_id)
    return {"item": updated}


@app.delete("/api/items/{item_id}", status_code=204)
def remove_item(item_id: int) -> None:
    logger.info("DELETE /api/items/%s", item_id)
    deleted = delete_schedule_item(database, item_id)
    if not deleted:
        logger.warning("DELETE /api/items/%s → 404 not found", item_id)
        raise HTTPException(status_code=404, detail="Item not found")


@app.get("/api/dashboard")
def dashboard() -> dict[str, object]:
    logger.info("GET /api/dashboard")
    stats = get_dashboard_stats(database)
    return stats


@app.get("/api/items/search")
def search_items(
    search: str = Query(default="", description="Поиск по проекту, ревизии, статусу и др."),
    sort_field: str = Query(default="event_date", description="Поле для сортировки"),
    sort_order: str = Query(default="asc", description="asc или desc"),
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    size: int = Query(default=25, ge=1, le=200, description="Размер страницы"),
) -> dict[str, object]:
    offset = (page - 1) * size
    all_items, total = search_schedule_items(
        database,
        search=search,
        sort_field=sort_field,
        sort_order=sort_order,
        limit=size,
        offset=offset,
    )
    logger.debug("GET /api/items/search '%s' page=%d → %d rows (total=%d)", search, page, len(all_items), total)
    return {"items": all_items, "total": total, "page": page, "size": size, "search": search}


@app.post("/api/sync/push")
def sync_push() -> dict[str, object]:
    logger.info("POST /api/sync/push started")
    try:
        items = list_schedule_items(database)
        logger.info("Pushing %d rows to Google Sheets", len(items))
        result = push_rows_to_sheet(items)
        logger.info("Push completed: %s", result)
        return {"ok": True, **result}
    except RuntimeError as exc:
        logger.error("Push failed (config): %s", exc)
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})
    except Exception as exc:
        logger.error("Push failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})


@app.post("/api/sync/pull")
def sync_pull() -> dict[str, object]:
    logger.info("POST /api/sync/pull started")
    try:
        rows = read_rows_from_sheet()
        logger.info("Pulled %d rows from Google Sheets", len(rows))
        replace_all_schedule_items(database, rows)
        logger.info("Pull completed, %d rows imported", len(rows))
        return {"ok": True, "rows_imported": len(rows)}
    except RuntimeError as exc:
        logger.error("Pull failed (config): %s", exc)
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})
    except Exception as exc:
        logger.error("Pull failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})


@app.get("/api/audit")
def audit_logs(
    page: int = Query(default=1, ge=1, description="Номер страницы"),
    size: int = Query(default=50, ge=1, le=200, description="Размер страницы"),
    action: str | None = Query(default=None, description="Фильтр по типу действия"),
) -> dict[str, object]:
    offset = (page - 1) * size
    logs, total = get_audit_logs(
        database,
        limit=size,
        offset=offset,
        action_filter=action,
    )
    logger.debug("GET /api/audit page=%d size=%d → %d logs (total=%d)", page, size, len(logs), total)
    return {"logs": logs, "total": total, "page": page, "size": size, "action": action}


@app.get("/api/export/excel")
def export_excel(
    search: str = Query(default="", description="Поиск (опционально)"),
) -> StreamingResponse:
    logger.info("GET /api/export/excel search='%s'", search)
    try:
        if search:
            items, _ = search_schedule_items(database, search=search, limit=None)
        else:
            items = list_schedule_items(database)

        excel_file = generate_excel(items, title="Расписание ревизий")

        filename = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        logger.error("Excel export failed: %s", exc, exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(exc)})

