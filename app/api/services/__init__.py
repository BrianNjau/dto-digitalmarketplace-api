from .prices import PricesService
from .audit import AuditService, AuditTypes
from .assessments import AssessmentsService
from .domain import DomainService
from .briefs import BriefsService
from .suppliers import SuppliersService
from .lots import LotsService
from .brief_responses import BriefResponsesService
from .brief_responses_contact import BriefResponseContactService

prices = PricesService()
audit_service = AuditService()
assessments = AssessmentsService()
domain_service = DomainService()
briefs = BriefsService()
suppliers = SuppliersService()
lots_service = LotsService()
brief_responses_service = BriefResponsesService()
brief_responses_contact_service = BriefResponseContactService()
