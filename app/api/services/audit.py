from app.api.helpers import Service
from app.models import AuditEvent
from enum import Enum
import rollbar


class AuditService(Service):
    __model__ = AuditEvent

    def __init__(self, *args, **kwargs):
        super(AuditService, self).__init__(*args, **kwargs)


class AuditTypes(Enum):
    update_price = 'update_price'
    update_brief_response = "update_brief_response"
