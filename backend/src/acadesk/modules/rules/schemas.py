import uuid
from datetime import datetime, time
from enum import StrEnum

from pydantic import BaseModel, Field

from acadesk.core.security import Role
from acadesk.modules.messaging.schemas import NoticeKind


class BillingStage(BaseModel):
    stage: int = Field(ge=1)
    days_after_due: int = Field(ge=0)
    requires_approval: bool


class WindowRule(BaseModel):
    window_days: int = Field(ge=1)
    count: int = Field(ge=1)


class RuleSettings(BaseModel):
    billing_stages: list[BillingStage] = [
        BillingStage(stage=1, days_after_due=1, requires_approval=False),
        BillingStage(stage=2, days_after_due=3, requires_approval=False),
        BillingStage(stage=3, days_after_due=7, requires_approval=True),
    ]
    repeated_absence: WindowRule = WindowRule(window_days=14, count=3)
    homework_missing: WindowRule = WindowRule(window_days=14, count=2)
    send_window_start: time = time(9, 0)
    send_window_end: time = time(21, 0)
    daily_cap_per_guardian: int = Field(2, ge=1)
    use_business_days: bool = Field(False, description="수납 단계 일수를 영업일로 셈 (캘린더 사용)")
    bundle_siblings: bool = Field(True, description="같은 보호자에게 같은 날 가는 안내를 한 통으로")
    auto_send_enabled: bool = Field(False, description="꺼 두면 모든 안내가 승인함을 거친다")
    approval_roles: dict[NoticeKind, list[Role]] = {
        NoticeKind.BILLING_REMINDER: [Role.OWNER, Role.MANAGER],
        NoticeKind.ABSENCE: [Role.OWNER, Role.MANAGER, Role.TEACHER],
        NoticeKind.REPEATED_ABSENCE: [Role.OWNER, Role.MANAGER, Role.TEACHER],
        NoticeKind.HOMEWORK: [Role.OWNER, Role.MANAGER, Role.TEACHER],
        NoticeKind.CORRECTION: [Role.OWNER, Role.MANAGER],
    }
    late_entry_minutes: int = Field(
        30, ge=0, description="수업 시작 후 이 시간이 지나 입력된 출결은 확인 필요"
    )
    alert_escalation_minutes: int = Field(
        20, ge=1, description="긴급 결석 알림 미확인 시 상위자에게"
    )


class RuleRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class RuleRunCreate(BaseModel):
    dry_run: bool = Field(True, description="true면 후보를 저장하지 않고 결과만 보여줌")
    kinds: list[NoticeKind] | None = None


class RuleRunOut(BaseModel):
    id: uuid.UUID
    status: RuleRunStatus
    dry_run: bool
    trigger: str = Field(description="schedule 또는 manual")
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_count: int = 0
    held_count: int = 0
    skipped_duplicate_count: int = 0
    error: str | None = None
