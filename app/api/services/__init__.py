from .application import ApplicationService
from .audit import AuditService, AuditTypes
from .assessments import AssessmentsService
from .domain import DomainService
from .briefs import BriefsService
from .suppliers import SuppliersService
from .lots import LotsService
from .brief_overview import BriefOverviewService
from .brief_responses import BriefResponsesService
from .users import UsersService
from .key_value import KeyValueService
from .frameworks import FrameworksService

application_service = ApplicationService()
audit_service = AuditService()
audit_types = AuditTypes
assessments = AssessmentsService()
domain_service = DomainService()
briefs = BriefsService()
suppliers = SuppliersService()
lots_service = LotsService()
brief_overview_service = BriefOverviewService()
brief_responses_service = BriefResponsesService()
users = UsersService()
key_values_service = KeyValueService()
frameworks_service = FrameworksService()
