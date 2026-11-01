import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from acadesk.api.deps import MVP, STAGE3, CurrentUserDep, access
from acadesk.core.errors import not_implemented
from acadesk.core.schemas import Page, PageParams, page_params
from acadesk.core.security import STAFF_ADMIN

from .schemas import (
    ColumnMappingBody,
    FieldSpec,
    ImportBatchOut,
    ImportKind,
    ImportRowOut,
    ImportStatus,
    RowStatus,
    SheetImportBody,
)

router = APIRouter(prefix="/imports", tags=["업로드"])

Paging = Annotated[PageParams, Depends(page_params)]


@router.get(
    "/kinds/{kind}/fields",
    summary="업로드 종류별 필드 목록",
    description="열 매핑 화면과 CSV 양식 안내에 쓴다.",
    **access(MVP, *STAFF_ADMIN),
)
def list_fields(user: CurrentUserDep, kind: ImportKind) -> list[FieldSpec]:
    raise not_implemented()


@router.post(
    "",
    summary="CSV·엑셀 업로드",
    description="원본 파일은 비공개 저장소에 두고 검사를 시작한다. 업로드 1회 = 배치 1건. "
    "열 이름을 자동으로 맞추지 못하면 mapping_required 상태가 된다.",
    status_code=status.HTTP_202_ACCEPTED,
    **access(MVP, *STAFF_ADMIN),
)
def upload(
    user: CurrentUserDep,
    kind: Annotated[ImportKind, Form()],
    file: Annotated[UploadFile, File(description=".csv, .xlsx")],
) -> ImportBatchOut:
    raise not_implemented()


@router.post(
    "/sheets",
    summary="구글 시트에서 가져오기",
    status_code=status.HTTP_202_ACCEPTED,
    **access(STAGE3, *STAFF_ADMIN),
)
def import_sheet(user: CurrentUserDep, body: SheetImportBody) -> ImportBatchOut:
    raise not_implemented()


@router.get("", summary="업로드 기록", **access(MVP, *STAFF_ADMIN))
def list_imports(
    user: CurrentUserDep,
    paging: Paging,
    kind: ImportKind | None = None,
    status_: Annotated[ImportStatus | None, Query(alias="status")] = None,
) -> Page[ImportBatchOut]:
    raise not_implemented()


@router.get("/{import_id}", summary="업로드 상태", **access(MVP, *STAFF_ADMIN))
def get_import(user: CurrentUserDep, import_id: uuid.UUID) -> ImportBatchOut:
    raise not_implemented()


@router.get("/{import_id}/rows", summary="행별 검사 결과", **access(MVP, *STAFF_ADMIN))
def list_rows(
    user: CurrentUserDep,
    import_id: uuid.UUID,
    paging: Paging,
    status_: Annotated[RowStatus | None, Query(alias="status")] = None,
) -> Page[ImportRowOut]:
    raise not_implemented()


@router.put(
    "/{import_id}/mapping",
    summary="열 매핑 저장 후 다시 검사",
    description="같은 학원이 같은 열 이름으로 다시 올리면 저장한 매핑을 자동으로 쓴다.",
    status_code=status.HTTP_202_ACCEPTED,
    **access(MVP, *STAFF_ADMIN),
)
def set_mapping(
    user: CurrentUserDep, import_id: uuid.UUID, body: ColumnMappingBody
) -> ImportBatchOut:
    raise not_implemented()


@router.post(
    "/{import_id}/commit",
    summary="검사 통과한 행 반영",
    description="ok·warning·duplicate 행만 외부 키로 upsert한다. error 행은 확인 필요함에 남는다. "
    "반영 뒤 형제 연결 후보와 입금자명 매칭 후보를 만든다.",
    **access(MVP, *STAFF_ADMIN),
)
def commit_import(user: CurrentUserDep, import_id: uuid.UUID) -> ImportBatchOut:
    raise not_implemented()


@router.delete(
    "/{import_id}",
    summary="반영 전 업로드 버리기",
    status_code=status.HTTP_204_NO_CONTENT,
    **access(MVP, *STAFF_ADMIN),
)
def discard_import(user: CurrentUserDep, import_id: uuid.UUID) -> None:
    raise not_implemented()


routers = [router]
