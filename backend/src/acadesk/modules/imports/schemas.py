import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ImportKind(StrEnum):
    STUDENTS = "students"  # 학생 + 보호자
    INVOICES = "invoices"  # 청구
    PAYMENTS = "payments"  # 납부
    ATTENDANCE = "attendance"
    HOMEWORK = "homework"
    BANK_DEPOSITS = "bank_deposits"  # 통장 입금 내역 → 입금자명 매칭


class ImportStatus(StrEnum):
    UPLOADED = "uploaded"
    MAPPING_REQUIRED = "mapping_required"  # 열 이름을 자동으로 못 맞춤
    VALIDATING = "validating"
    VALIDATED = "validated"  # 행별 검사 끝, 반영 대기
    COMMITTED = "committed"
    DISCARDED = "discarded"
    FAILED = "failed"


class ImportBatchOut(BaseModel):
    id: uuid.UUID
    kind: ImportKind
    source: str = Field(description="file 또는 google_sheets")
    filename: str | None = None
    status: ImportStatus
    row_count: int = 0
    ok_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    duplicate_count: int = 0
    column_mapping: dict[str, str] | None = Field(None, description="파일 열 이름 → 필드")
    created_by: uuid.UUID
    created_at: datetime
    committed_at: datetime | None = None


class RowStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"  # 반영은 되지만 확인 권장 (예: 수업 시작 후 늦게 입력된 출결)
    ERROR = "error"  # 반영 안 됨, 확인 필요함으로 감
    DUPLICATE = "duplicate"  # 같은 외부 키가 이미 있음 → 갱신


class ImportRowOut(BaseModel):
    row_number: int
    status: RowStatus
    data: dict[str, str | None]
    messages: list[str] = []


class ColumnMappingBody(BaseModel):
    mapping: dict[str, str] = Field(description="파일 열 이름 → 필드 이름")


class FieldSpec(BaseModel):
    field: str
    label: str
    required: bool
    example: str | None = None


class SheetImportBody(BaseModel):
    kind: ImportKind
    sheet_url: str
    worksheet: str | None = None
