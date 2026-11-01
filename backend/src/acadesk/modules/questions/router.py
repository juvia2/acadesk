import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from acadesk.api.deps import MVP, STAGE2, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import MEMBERS, Role

from .schemas import (
    QuestionCategory,
    QuestionCreate,
    QuestionDetail,
    QuestionMessageCreate,
    QuestionMessageOut,
    QuestionOut,
    QuestionStatus,
    QuestionUpdate,
)

router = APIRouter(prefix="/questions", tags=["질의응답"])

Paging = Annotated[PageParams, Depends(page_params)]


@router.get(
    "",
    summary="질문 목록",
    description="학생·학부모는 자기가 쓴 질문, 교사는 배정된 질문과 자기 강의 질문, 관리자는 전체. "
    "학부모는 자녀가 교사와 나눈 질문을 볼 수 없다.",
    **access(MVP, *MEMBERS),
)
def list_questions(
    user: CurrentUserDep,
    paging: Paging,
    status_: Annotated[QuestionStatus | None, Query(alias="status")] = None,
    category: QuestionCategory | None = None,
    lecture_id: uuid.UUID | None = None,
    assigned_to_me: bool = False,
) -> Page[QuestionOut]:
    raise not_implemented()


@router.get(
    "/public",
    summary="같은 강의 공개 질문 (익명)",
    description="학생이 공개로 바꾼 질문을 같은 강의 학생이 본다. 작성자 이름은 보이지 않는다.",
    **access(STAGE2, Role.STUDENT),
)
def list_public_questions(
    user: CurrentUserDep, paging: Paging, lecture_id: uuid.UUID
) -> Page[QuestionOut]:
    raise not_implemented()


@router.post(
    "",
    summary="질문하기 (학생·학부모)",
    description="lecture_id를 고르면 그 강의 교사에게, 아니면 학원 관리자에게 간다. 받는 사람에게 앱 푸시.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, Role.STUDENT, Role.PARENT),
)
def create_question(user: CurrentUserDep, body: QuestionCreate) -> QuestionDetail:
    raise not_implemented()


@router.get("/{question_id}", summary="질문 상세·대화", **access(MVP, *MEMBERS))
def get_question(user: CurrentUserDep, question_id: uuid.UUID) -> QuestionDetail:
    raise not_implemented()


@router.post(
    "/{question_id}/messages",
    summary="답변·추가 질문",
    description="교사가 답하면 상태가 answered, 질문자가 다시 쓰면 open으로 바뀐다.",
    status_code=status.HTTP_201_CREATED,
    **access(MVP, *MEMBERS),
)
def add_message(
    user: CurrentUserDep, question_id: uuid.UUID, body: QuestionMessageCreate
) -> QuestionMessageOut:
    raise not_implemented()


@router.post(
    "/{question_id}/read",
    summary="읽음 표시",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *MEMBERS),
)
def mark_read(user: CurrentUserDep, question_id: uuid.UUID) -> None:
    raise not_implemented()


@router.patch(
    "/{question_id}",
    summary="종료·담당 변경·공개 전환",
    **access(MVP, *MEMBERS),
)
def update_question(
    user: CurrentUserDep, question_id: uuid.UUID, body: QuestionUpdate
) -> QuestionOut:
    raise not_implemented()


routers = [router]
