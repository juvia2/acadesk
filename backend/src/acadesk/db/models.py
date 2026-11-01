"""모든 모델을 한 번에 불러온다. Alembic과 테스트가 Base.metadata를 채울 때 쓴다."""

from acadesk.ai import models as ai  # noqa: F401
from acadesk.db.base import Base
from acadesk.modules.academies import models as academies  # noqa: F401
from acadesk.modules.approvals import models as approvals  # noqa: F401
from acadesk.modules.attendance import models as attendance  # noqa: F401
from acadesk.modules.audit import models as audit  # noqa: F401
from acadesk.modules.billing import models as billing  # noqa: F401
from acadesk.modules.documents import models as documents  # noqa: F401
from acadesk.modules.homework import models as homework  # noqa: F401
from acadesk.modules.imports import models as imports  # noqa: F401
from acadesk.modules.messaging import models as messaging  # noqa: F401
from acadesk.modules.rules import models as rules  # noqa: F401
from acadesk.modules.students import models as students  # noqa: F401

metadata = Base.metadata
