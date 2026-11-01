"""질의응답·상담. 질문 하나 = 스레드 하나.

학생–교사 스레드는 학부모에게 보이지 않는다 (기획안 v2 6장).
"""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from acadesk.core.security import Role
from acadesk.modules.notices.schemas import AttachmentOut


class QuestionCategory(StrEnum):
    STUDY = "study"  # 학습 질문
    COUNSEL = "counsel"  # 상담
    SCHEDULE = "schedule"  # 일정·보강
    OTHER = "other"


class QuestionStatus(StrEnum):
    OPEN = "open"  # 답변 대기
    ANSWERED = "answered"
    CLOSED = "closed"


class QuestionVisibility(StrEnum):
    PRIVATE = "private"
    LECTURE_PUBLIC = "lecture_public"  # 같은 강의 학생에게 익명 공개 (2단계)


class QuestionMessageOut(BaseModel):
    id: uuid.UUID
    author_name: str
    author_role: Role
    body: str
    attachments: list[AttachmentOut] = []
    is_mine: bool
    created_at: datetime


class QuestionOut(BaseModel):
    id: uuid.UUID
    title: str
    category: QuestionCategory
    status: QuestionStatus
    visibility: QuestionVisibility
    author_role: Role
    author_name: str | None = Field(None, description="공개 질문을 다른 학생이 볼 때는 null")
    student_id: uuid.UUID = Field(description="어느 학생에 관한 질문인지 (학부모는 자녀)")
    student_name: str | None = None
    lecture_id: uuid.UUID | None = None
    lecture_name: str | None = None
    assignee_id: uuid.UUID | None = Field(None, description="답변할 교사. 비면 학원 관리자")
    assignee_name: str | None = None
    unread_count: int = 0
    last_message_at: datetime
    created_at: datetime


class QuestionDetail(QuestionOut):
    messages: list[QuestionMessageOut]


class QuestionCreate(BaseModel):
    title: str = Field(max_length=200)
    body: str = Field(max_length=5000)
    category: QuestionCategory = QuestionCategory.STUDY
    lecture_id: uuid.UUID | None = Field(None, description="고르면 그 강의 교사에게 배정")
    student_id: uuid.UUID | None = Field(
        None, description="학부모: 어느 자녀에 관한 질문인지 (필수)"
    )
    attachment_ids: list[uuid.UUID] = []


class QuestionMessageCreate(BaseModel):
    body: str = Field(max_length=5000)
    attachment_ids: list[uuid.UUID] = []


class QuestionUpdate(BaseModel):
    status: QuestionStatus | None = None
    assignee_id: uuid.UUID | None = Field(None, description="관리자만 변경")
    visibility: QuestionVisibility | None = Field(
        None, description="작성 학생만 공개로 바꿀 수 있음"
    )
