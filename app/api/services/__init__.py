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
from .teams import TeamService
from .team_members import TeamMemberService
from .team_member_permissions import TeamMemberPermissionService
from .work_order import WorkOrderService
from .brief_question import BriefQuestionService
from .brief_clarification_question import BriefClarificationQuestionService
from .brief_response_download import BriefResponseDownloadService

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
team_service = TeamService()
team_member_service = TeamMemberService()
team_member_permission_service = TeamMemberPermissionService()
user_claims_service = UserClaimService()
work_order_service = WorkOrderService()
brief_question_service = BriefQuestionService()
brief_clarification_question_service = BriefClarificationQuestionService()
brief_response_download_service = BriefResponseDownloadService()
