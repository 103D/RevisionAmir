"""Audit logging module for tracking changes to schedule items."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger("revision.audit")


# Audit action types
ACTION_CREATE = "create"
ACTION_UPDATE = "update"
ACTION_DELETE = "delete"
ACTION_REPLACE = "replace"  # For bulk operations like pull from sheets


def get_audit_schema() -> str:
    """Return SQL schema for audit_log table."""
    return """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    item_id INTEGER,
    old_data TEXT,  -- JSON string of old values (for update/delete)
    new_data TEXT,  -- JSON string of new values (for create/update)
    user_info TEXT DEFAULT 'system',  -- Could be user ID or 'system' for automated changes
    details TEXT  -- Additional details about the change
)
"""


def log_change(
    connection,
    action: str,
    item_id: int | None = None,
    old_data: dict[str, Any] | None = None,
    new_data: dict[str, Any] | None = None,
    user_info: str = "system",
    details: str | None = None,
) -> None:
    """Log a change to the audit table."""
    try:
        old_json = json.dumps(old_data, ensure_ascii=False, default=str) if old_data else None
        new_json = json.dumps(new_data, ensure_ascii=False, default=str) if new_data else None
        
        connection.execute(
            """
            INSERT INTO audit_log (action, item_id, old_data, new_data, user_info, details)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (action, item_id, old_json, new_json, user_info, details),
        )
        # Don't commit here - let the calling function handle transaction
        logger.debug("Audit logged: action=%s, item_id=%s", action, item_id)
    except Exception as e:
        logger.error("Failed to log audit: %s", e, exc_info=True)
        # Don't raise - audit logging shouldn't break main functionality


def log_create(connection, item_id: int, new_data: dict[str, Any], user_info: str = "system") -> None:
    """Log creation of a new item."""
    log_change(
        connection,
        action=ACTION_CREATE,
        item_id=item_id,
        new_data=new_data,
        user_info=user_info,
        details=f"Created item '{new_data.get('project', '')}'",
    )


def log_update(
    connection,
    item_id: int,
    old_data: dict[str, Any],
    new_data: dict[str, Any],
    user_info: str = "system",
) -> None:
    """Log update of an existing item."""
    # Create summary of changes
    changed_fields = []
    for key in new_data:
        if key in old_data and old_data[key] != new_data[key]:
            changed_fields.append(key)
    
    details = f"Updated fields: {', '.join(changed_fields)}" if changed_fields else "No fields changed"
    
    log_change(
        connection,
        action=ACTION_UPDATE,
        item_id=item_id,
        old_data=old_data,
        new_data=new_data,
        user_info=user_info,
        details=details,
    )


def log_delete(
    connection,
    item_id: int,
    old_data: dict[str, Any],
    user_info: str = "system",
) -> None:
    """Log deletion of an item."""
    log_change(
        connection,
        action=ACTION_DELETE,
        item_id=item_id,
        old_data=old_data,
        user_info=user_info,
        details=f"Deleted item '{old_data.get('project', '')}'",
    )


def log_replace(connection, count: int, user_info: str = "system") -> None:
    """Log bulk replace operation (e.g., pull from sheets)."""
    log_change(
        connection,
        action=ACTION_REPLACE,
        user_info=user_info,
        details=f"Replaced all {count} items",
    )
