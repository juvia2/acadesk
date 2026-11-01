import uuid
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HomeworkOut(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID
    title: str
    due_date: date
    created_by: uuid.UUID
    created_at: datetime
    missing_count: int = 0


class HomeworkCreate(BaseModel):
    class_id: uuid.UUID
    title: str
    due_date: date


class HomeworkUpdate(BaseModel):
    title: str | None = None
    due_date: date | None = None


class SubmissionStatus(StrEnum):
    DONE = "done"
    PARTIAL = "partial"
    MISSING = "missing"


class SubmissionOut(BaseModel):
    student_id: uuid.UUID
    student_name: str
    status: SubmissionStatus
    note: str | None = None
    recorded_at: datetime


class SubmissionItem(BaseModel):
    student_id: uuid.UUID
    status: SubmissionStatus
    note: str | None = None


class SubmissionBatch(BaseModel):
    items: list[SubmissionItem] = Field(min_length=1)
