import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class DocumentStatus(StrEnum):
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class DocumentOut(BaseModel):
    id: uuid.UUID
    kind: str = "billing_notice"
    approval_id: uuid.UUID
    status: DocumentStatus
    created_at: datetime


class BillingNoticeCreate(BaseModel):
    approval_id: uuid.UUID


class DocumentLink(BaseModel):
    url: str
    expires_at: datetime
