from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

from .audit import (
    log_create,
    log_delete,
    log_replace,
    log_update,
    get_audit_schema,
)
from .seed import schedule_seed

logger = logging.getLogger("revision.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS schedule_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month TEXT NOT NULL,
    project TEXT NOT NULL,
    revision_info TEXT NOT NULL,
    event_date TEXT NOT NULL,
    weekday TEXT NOT NULL,
    inspection_type TEXT NOT NULL,
    status TEXT NOT NULL,
    amount_planned REAL,
    amount_actual REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def open_database(database_path: str) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(SCHEMA)
    connection.execute(get_audit_schema())
    logger.info("Database opened: %s", database_path)

    count = connection.execute("SELECT COUNT(*) FROM schedule_items").fetchone()[0]
    if count == 0:
        logger.info("Database empty, seeding with %d rows", len(schedule_seed))
        replace_all_schedule_items(connection, schedule_seed)
    else:
        logger.info("Database has %d existing rows", count)

    return connection


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None

    return {
        "id": row["id"],
        "year": row["year"],
        "month": row["month"],
        "project": row["project"],
        "revision_info": row["revision_info"],
        "event_date": row["event_date"],
        "weekday": row["weekday"],
        "inspection_type": row["inspection_type"],
        "status": row["status"],
        "amount_planned": row["amount_planned"],
        "amount_actual": row["amount_actual"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_schedule_items(connection: sqlite3.Connection, limit: int | None = None, offset: int = 0) -> list[dict[str, Any]]:
    query = "SELECT * FROM schedule_items ORDER BY event_date ASC, id ASC"
    params: list[Any] = []
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    rows = connection.execute(query, params).fetchall()
    return [row_to_dict(row) for row in rows]


def count_schedule_items(connection: sqlite3.Connection) -> int:
    row = connection.execute("SELECT COUNT(*) FROM schedule_items").fetchone()
    return int(row[0]) if row else 0


def get_schedule_item(connection: sqlite3.Connection, item_id: int) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM schedule_items WHERE id = ?",
        (item_id,),
    ).fetchone()
    return row_to_dict(row)


def create_schedule_item(connection: sqlite3.Connection, item: dict[str, Any]) -> dict[str, Any]:
    logger.debug("Creating item: project=%s, date=%s", item.get("project"), item.get("event_date"))
    cursor = connection.execute(
        """
        INSERT INTO schedule_items (
            year, month, project, revision_info, event_date, weekday,
            inspection_type, status, amount_planned, amount_actual
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item["year"],
            item["month"],
            item["project"],
            item["revision_info"],
            item["event_date"],
            item["weekday"],
            item["inspection_type"],
            item["status"],
            item["amount_planned"],
            item["amount_actual"],
        ),
    )
    item_id = cursor.lastrowid
    new_data = get_schedule_item(connection, item_id)
    log_create(connection, item_id, new_data)
    connection.commit()
    return new_data

def update_schedule_item(
    connection: sqlite3.Connection, item_id: int, item: dict[str, Any]
) -> dict[str, Any] | None:
    logger.debug("Updating item id=%s", item_id)
    old_data = get_schedule_item(connection, item_id)
    connection.execute(
        """
        UPDATE schedule_items
        SET year = ?,
            month = ?,
            project = ?,
            revision_info = ?,
            event_date = ?,
            weekday = ?,
            inspection_type = ?,
            status = ?,
            amount_planned = ?,
            amount_actual = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            item["year"],
            item["month"],
            item["project"],
            item["revision_info"],
            item["event_date"],
            item["weekday"],
            item["inspection_type"],
            item["status"],
            item["amount_planned"],
            item["amount_actual"],
            item_id,
        ),
    )
    new_data = get_schedule_item(connection, item_id)
    log_update(connection, item_id, old_data, new_data)
    connection.commit()
    return new_data


def delete_schedule_item(connection: sqlite3.Connection, item_id: int) -> bool:
    old_data = get_schedule_item(connection, item_id)
    cursor = connection.execute("DELETE FROM schedule_items WHERE id = ?", (item_id,))
    deleted = cursor.rowcount > 0
    if deleted and old_data:
        log_delete(connection, item_id, old_data)
    connection.commit()
    logger.debug("Deleted item id=%s → %s", item_id, "found" if deleted else "not found")
    return deleted


def replace_all_schedule_items(
    connection: sqlite3.Connection, rows: list[dict[str, Any]]
) -> None:
    cursor = connection.execute("SELECT COUNT(*) FROM schedule_items")
    old_count = cursor.fetchone()[0]
    logger.info("Replacing all items: %d old → %d new", old_count, len(rows))

    try:
        connection.execute("DELETE FROM schedule_items")
        connection.executemany(
            """
            INSERT INTO schedule_items (
                year, month, project, revision_info, event_date, weekday,
                inspection_type, status, amount_planned, amount_actual
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["year"],
                    row["month"],
                    row["project"],
                    row["revision_info"],
                    row["event_date"],
                    row["weekday"],
                    row["inspection_type"],
                    row["status"],
                    row["amount_planned"],
                    row["amount_actual"],
                )
                for row in rows
            ],
        )
        log_replace(connection, len(rows))
        connection.commit()
        logger.info("Replaced %d items successfully", len(rows))
    except Exception:
        connection.rollback()
        logger.error("Replace failed, rolled back %d old rows", old_count)
        raise


def get_dashboard_stats(connection: sqlite3.Connection) -> dict[str, Any]:
    """Return aggregate statistics for the dashboard."""
    total_items = count_schedule_items(connection)

    sum_row = connection.execute(
        "SELECT COALESCE(SUM(amount_planned), 0) AS total_planned, COALESCE(SUM(amount_actual), 0) AS total_actual FROM schedule_items"
    ).fetchone()
    total_planned = sum_row["total_planned"] if sum_row else 0
    total_actual = sum_row["total_actual"] if sum_row else 0

    status_rows = connection.execute(
        "SELECT status, COUNT(*) AS cnt FROM schedule_items GROUP BY status ORDER BY cnt DESC"
    ).fetchall()
    status_breakdown = {row["status"]: row["cnt"] for row in status_rows}

    project_rows = connection.execute(
        "SELECT project, COUNT(*) AS cnt FROM schedule_items GROUP BY project ORDER BY cnt DESC"
    ).fetchall()
    unique_projects = [{"project": row["project"], "count": row["cnt"]} for row in project_rows]

    today = __import__("datetime").date.today().isoformat()
    upcoming = connection.execute(
        "SELECT COUNT(*) FROM schedule_items WHERE event_date >= ?", (today,)
    ).fetchone()[0] or 0
    overdue = connection.execute(
        "SELECT COUNT(*) FROM schedule_items WHERE event_date < ?", (today,)
    ).fetchone()[0] or 0

    return {
        "totalItems": total_items,
        "totalPlanned": total_planned,
        "totalActual": total_actual,
        "statusBreakdown": status_breakdown,
        "uniqueProjects": unique_projects,
        "projectsCount": len(unique_projects),
        "upcoming": upcoming,
        "overdue": overdue,
    }


def search_schedule_items(
    connection: sqlite3.Connection,
    search: str = "",
    sort_field: str = "event_date",
    sort_order: str = "asc",
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Search and sort schedule items. Returns (items, total_count)."""
    allowed_sort_fields = {
        "year", "month", "project", "revision_info", "event_date",
        "weekday", "inspection_type", "status", "amount_planned", "amount_actual",
    }
    if sort_field not in allowed_sort_fields:
        sort_field = "event_date"
    sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"

    order_clause = f"ORDER BY {sort_field} {sort_direction}, id ASC"

    if search:
        like = f"%{search}%"
        where = "WHERE project LIKE ? OR revision_info LIKE ? OR status LIKE ? OR inspection_type LIKE ? OR month LIKE ?"
        params: list[Any] = [like, like, like, like, like]
    else:
        where = ""
        params = []

    count_row = connection.execute(

        f"SELECT COUNT(*) FROM schedule_items {where}", params
    ).fetchone()
    total = int(count_row[0]) if count_row else 0

    query = f"SELECT * FROM schedule_items {where} {order_clause}"
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    rows = connection.execute(query, params).fetchall()
    items = [row_to_dict(row) for row in rows]
    return items, total


def get_audit_logs(
    connection: sqlite3.Connection,
    limit: int | None = None,
    offset: int = 0,
    action_filter: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Return audit logs with optional filtering."""
    connection.execute(get_audit_schema())

    where_clauses: list[str] = []
    params: list[Any] = []

    if action_filter:
        where_clauses.append("action = ?")
        params.append(action_filter)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    count_row = connection.execute(
        f"SELECT COUNT(*) FROM audit_log {where_sql}",
        params,
    ).fetchone()
    total = int(count_row[0]) if count_row else 0

    query = f"SELECT * FROM audit_log {where_sql} ORDER BY timestamp DESC, id DESC"
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    rows = connection.execute(query, params).fetchall()
    logs = [
        {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "action": row["action"],
            "item_id": row["item_id"],
            "old_data": row["old_data"],
            "new_data": row["new_data"],
            "user_info": row["user_info"],
            "details": row["details"],
        }
        for row in rows
    ]
    return logs, total

