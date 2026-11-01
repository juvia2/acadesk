import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class NoticeAudience(StrEnum):
    STUDENTS = "students"
    PARENTS = "parents"
    ALL = "all"


class AttachmentOut(BaseModel):
    id: uuid.UUID
    filename: str
    size: int
    content_type: str


class NoticeOut(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    lecture_id: uuid.UUID | None = Field(None, description="null = 학원 전체 공지")
    lecture_name: str | None = None
    audience: NoticeAudience
    pinned: bool = False
    attachments: list[AttachmentOut] = []
    author_id: uuid.UUID
    author_name: str
    published_at: datetime
    updated_at: datetime | None = None
    read: bool = Field(False, description="요청한 사용자가 읽었는지")
    read_count: int | None = Field(None, description="직원에게만: 읽은 사람 수")
    target_count: int | None = Field(None, description="직원에게만: 받을 사람 수")


class NoticeCreate(BaseModel):
    title: str = Field(max_length=200)
    body: str = Field(max_length=10000)
    lecture_id: uuid.UUID | None = Field(None, description="교사는 자기 강의만 가능")
    audience: NoticeAudience = NoticeAudience.ALL
    pinned: bool = False
    attachment_ids: list[uuid.UUID] = []
    notify: bool = Field(True, description="앱 푸시 보내기")


class NoticeUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    body: str | None = Field(None, max_length=10000)
    pinned: bool | None = None
    attachment_ids: list[uuid.UUID] | None = None


class ReaderOut(BaseModel):
    user_id: uuid.UUID
    name: str
    role: str
    student_name: str | None = Field(None, description="학부모면 자녀 이름")
    read_at: datetime | None = None


class NoticeReads(BaseModel):
    read: list[ReaderOut]
    unread: list[ReaderOut]
