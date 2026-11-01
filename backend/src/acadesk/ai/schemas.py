from enum import StrEnum


class AiTask(StrEnum):
    REPLY_CLASSIFICATION = "reply_classification"
    DRAFT = "draft"
    CONSULT_SUMMARY = "consult_summary"
    MISMATCH_DETECTION = "mismatch_detection"
    TRANSLATION = "translation"


class AiRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    NEEDS_REVIEW = "needs_review"  # 검증 실패 → 사람에게
    FAILED = "failed"
