from .agency import AgencyService
from .agreement import AgreementService
from .signed_agreement import SignedAgreementService
from .application import ApplicationService
from .audit import AuditService, AuditTypes
from .assessments import AssessmentsService
from .domain import DomainService
from .briefs import BriefsService
from .suppliers import SuppliersService
from .supplier_domain import SupplierDomainService
from .lots import LotsService
from .brief_responses import BriefResponsesService
from .users import UsersService
from .key_value import KeyValueService
from .publish import Publish
from .frameworks import FrameworksService
from .user_claims import UserClaimService
from .teams import TeamsService
from .team_members import TeamMembersService
from .team_member_permissions import TeamMemberPermissionsService
from .work_order import WorkOrderService
from .brief_question import BriefQuestionService

agency_service = AgencyService()
agreement_service = AgreementService()
signed_agreement_service = SignedAgreementService()
application_service = ApplicationService()
audit_service = AuditService()
audit_types = AuditTypes
assessments = AssessmentsService()
domain_service = DomainService()
briefs = BriefsService()
suppliers = SuppliersService()
supplier_domain_service = SupplierDomainService()
lots_service = LotsService()
brief_responses_service = BriefResponsesService()
users = UsersService()
key_values_service = KeyValueService()
publish = Publish()
frameworks_service = FrameworksService()
teams = TeamsService()
team_members = TeamMembersService()
team_member_permissions = TeamMemberPermissionsService()
user_claims_service = UserClaimService()
work_order_service = WorkOrderService()
brief_question_service = BriefQuestionService()
