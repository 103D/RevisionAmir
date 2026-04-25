from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


RevisionStatus = Literal["planned", "postponed"]


class FilialCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    first_revision_date: date
    shortage: float = Field(default=0, ge=0)
    revision_dates: list[date] = Field(default_factory=list)


class FilialUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    first_revision_date: Optional[date] = None
    shortage: Optional[float] = Field(default=None, ge=0)


class RevisionDatesUpdate(BaseModel):
    revision_dates: list[date] = Field(default_factory=list)


class NextRevisionUpdate(BaseModel):
    next_revision_date: date
    status: RevisionStatus = "planned"


class FilialOut(BaseModel):
    id: str
    name: str
    first_revision_date: date
    previous_revision_date: Optional[date] = None
    next_revision_date: Optional[date] = None
    next_revision_status: RevisionStatus = "planned"
    shortage: float = 0
    revision_shortages: dict[str, float] = Field(default_factory=dict)
    revision_dates: list[date] = Field(default_factory=list)
    revision_statuses: dict[str, RevisionStatus] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
