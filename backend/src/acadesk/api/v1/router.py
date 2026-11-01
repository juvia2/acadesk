from fastapi import APIRouter

from acadesk.api.v1 import ai, auth, dashboard, public, webhooks
from acadesk.modules.academies.router import routers as academies
from acadesk.modules.approvals.router import routers as approvals
from acadesk.modules.attendance.router import routers as attendance
from acadesk.modules.audit.router import routers as audit
from acadesk.modules.billing.router import routers as billing
from acadesk.modules.documents.router import routers as documents
from acadesk.modules.homework.router import routers as homework
from acadesk.modules.imports.router import routers as imports
from acadesk.modules.messaging.router import routers as messaging
from acadesk.modules.rules.router import routers as rules
from acadesk.modules.students.router import routers as students

api_router = APIRouter()

# 명세서와 Swagger에 나오는 순서
for r in [
    auth.router,
    dashboard.router,
    *academies,
    *students,
    *imports,
    *billing,
    *attendance,
    *homework,
    *rules,
    *approvals,
    *messaging,
    *documents,
    *audit,
    ai.router,
    webhooks.router,
    public.router,
]:
    api_router.include_router(r)
