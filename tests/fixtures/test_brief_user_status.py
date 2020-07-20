# -*- coding: utf-8 -*-
import pytest
import pendulum
import copy
from app.api.business.brief import BriefUserStatus
from app.models import db, Assessment, BriefAssessment, SupplierDomain, CaseStudy, BriefResponse


rfx_data = {
    'title': 'TEST',
    'organisation': 'ABC',
    'summary': 'TEST',
    'workingArrangements': 'TEST',
    'location': [
        'New South Wales'
    ],
    'sellerCategory': '1',
    'sellers': {
        '1': {
            'name': 'Test Supplier1'
        }
    },
    'evaluationType': [
        'Response template',
        'Written proposal'
    ],
    'proposalType': [
        'Breakdown of costs',
        'Résumés'
    ],
    'requirementsDocument': [
        'TEST.pdf'
    ],
    'responseTemplate': [
        'TEST2.pdf'
    ],
    'attachments': [
        'TEST3.pdf'
    ],
    'industryBriefing': 'TEST',
    'startDate': 'ASAP',
    'contractLength': 'TEST',
    'includeWeightings': True,
    'essentialRequirements': [
        {
            'criteria': 'TEST',
            'weighting': '55'
        },
        {
            'criteria': 'TEST 2',
            'weighting': '45'
        }
    ],
    'niceToHaveRequirements': [],
    'contactNumber': '0263635544'
}

atm_data = {
    'title': 'TEST',
    'closedAt': pendulum.today(tz='Australia/Sydney').add(days=14).format('%Y-%m-%d'),
    'organisation': 'ABC',
    'summary': 'TEST',
    'location': [
        'New South Wales'
    ],
    'sellerCategory': '',
    'openTo': 'all',
    'requestMoreInfo': 'no',
    'evaluationType': [],
    'attachments': [
        'TEST3.pdf'
    ],
    'industryBriefing': 'TEST',
    'startDate': 'ASAP',
    'includeWeightings': True,
    'evaluationCriteria': [
        {
            'criteria': 'TEST',
            'weighting': '55'
        },
        {
            'criteria': 'TEST 2',
            'weighting': '45'
        }
    ],
    'contactNumber': '0263635544',
    'timeframeConstraints': 'TEST',
    'backgroundInformation': 'TEST',
    'outcome': 'TEST',
    'endUsers': 'TEST',
    'workAlreadyDone': 'TEST'
}

specialist_data = {
    "securityClearanceOther": "",
    "startDate": "2020-10-20",
    "attachments": [
        "test.pdf"
    ],
    "preferredFormatForRates": "dailyRate",
    "evaluationType": [
        "Responses to selection criteria",
        "R\u00e9sum\u00e9s"
    ],
    "sellers": {},
    "contractLength": "2 years",
    "includeWeightingsNiceToHave": False,
    "securityClearanceCurrent": "",
    "essentialRequirements": [
        {
            "weighting": "",
            "criteria": "Python"
        }
    ],
    "contactNumber": "0412 345 678",
    "maxRate": "1000",
    "budgetRange": "",
    "securityClearance": "noneRequired",
    "sellerSelector": "allSellers",
    "sellerCategory": "6",
    "contractExtensions": "",
    "includeWeightingsEssential": False,
    "title": "Developer",
    "organisation": "Digital Transformation Agency",
    "internalReference": "",
    "niceToHaveRequirements": [
        {
            "weighting": "",
            "criteria": ""
        }
    ],
    "numberOfSuppliers": "3",
    "summary": "Code",
    "closedAt": "2020-09-10",
    "location": [
        "Australian Capital Territory",
        "New South Wales"
    ],
    "areaOfExpertise": "Software engineering and Development",
    "comprehensiveTerms": False,
    "securityClearanceObtain": "",
    "openTo": "all"
}

open_to_selected_specialist_data = {
    "areaOfExpertise": "Software engineering and Development",
    "attachments": [
        "test.pdf"
    ],
    "budgetRange": "",
    "closedAt": "2020-09-10",
    "comprehensiveTerms": False,
    "contactNumber": "0412 345 678",
    "contractExtensions": "",
    "contractLength": "2 years",
    "essentialRequirements": [
        {
            "weighting": "",
            "criteria": "Code"
        }
    ],
    "evaluationType": [
        "Responses to selection criteria",
        "Résumés"
    ],
    "includeWeightingsEssential": False,
    "includeWeightingsNiceToHave": False,
    "internalReference": "",
    "location": [
        "New South Wales",
        "Australian Capital Territory"
    ],
    "maxRate": "1000",
    "niceToHaveRequirements": [
        {
            "weighting": "",
            "criteria": ""
        }
    ],
    "numberOfSuppliers": "3",
    "openTo": "selected",
    "organisation": "Digital Transformation Agency",
    "preferredFormatForRates": "dailyRate",
    "securityClearance": "noneRequired",
    "securityClearanceCurrent": "",
    "securityClearanceObtain": "",
    "securityClearanceOther": "",
    "sellerCategory": "6",
    "sellerSelector": "someSellers",
    "sellers": {
        "1": {
            "name": "Test Supplier1"
        }
    },
    "startDate": "2020-10-20",
    "summary": "Code",
    "title": "Developer"
}

open_to_selected_specialist_data_not_invited = copy.copy(open_to_selected_specialist_data)
open_to_selected_specialist_data_not_invited['sellers'] = {
    '999': {
        'name': 'test'
    }
}

@pytest.fixture()
def supplier_domains(app, request, domains, suppliers):
    params = request.param if hasattr(request, 'param') else {}
    status = params['status'] if 'status' in params else 'assessed'
    price_status = params['price_status'] if 'price_status' in params else 'approved'
    with app.app_context():
        for domain in domains:
            db.session.add(SupplierDomain(
                supplier_id=suppliers[0].id,
                domain_id=domain.id,
                status=status,
                price_status=price_status
            ))
            db.session.flush()
        db.session.commit()
        yield SupplierDomain.query.all()


@pytest.fixture()
def assessments(app, supplier_domains):
    with app.app_context():
        for sd in supplier_domains:
            db.session.add(Assessment(
                supplier_domain_id=sd.id
            ))
            db.session.flush()
        db.session.commit()
        yield Assessment.query.all()


@pytest.fixture()
def brief_assessments(app, assessments):
    with app.app_context():
        for a in assessments:
            db.session.add(BriefAssessment(
                brief_id=1,
                assessment_id=a.id
            ))
            db.session.flush()
        db.session.commit()
        yield BriefAssessment.query.all()


@pytest.fixture()
def brief_response(app):
    with app.app_context():
        db.session.add(BriefResponse(
            id=1,
            brief_id=1,
            supplier_code=1,
            submitted_at=pendulum.now(),
            data={}
        ))

        db.session.commit()
        yield BriefResponse.query.get(1)


@pytest.mark.parametrize(
    'rfx_brief',
    [{'data': rfx_data}], indirect=True
)
def test_rfx_brief_user_status_selected_seller(rfx_brief, supplier_user, case_studies, brief_assessments):
    user_status = BriefUserStatus(rfx_brief, supplier_user)
    assert user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert user_status.is_assessed_for_category()
    assert not user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert not user_status.has_been_assessed_for_brief()
    assert user_status.can_respond()
    assert not user_status.has_responded()


@pytest.mark.parametrize(
    'rfx_brief',
    [{'data': rfx_data}], indirect=True
)
def test_rfx_brief_user_status_selected_seller_responded(rfx_brief, supplier_user, case_studies, brief_assessments,
                                                         brief_response):
    user_status = BriefUserStatus(rfx_brief, supplier_user)
    assert user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert user_status.is_assessed_for_category()
    assert not user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert not user_status.has_been_assessed_for_brief()
    assert user_status.can_respond()
    assert user_status.has_responded()


rfx_data_not_selected = copy.copy(rfx_data)
rfx_data_not_selected['sellers'] = {
    '999': {
        'name': 'test'
    }
}


@pytest.mark.parametrize(
    'rfx_brief',
    [{'data': rfx_data_not_selected}], indirect=True
)
def test_rfx_brief_user_status_non_selected_seller(rfx_brief, supplier_user, case_studies, brief_assessments):
    user_status = BriefUserStatus(rfx_brief, supplier_user)
    assert user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert user_status.is_assessed_for_category()
    assert not user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert not user_status.has_been_assessed_for_brief()
    assert not user_status.can_respond()
    assert not user_status.has_responded()


@pytest.mark.parametrize(
    'atm_brief',
    [{'data': atm_data}], indirect=True
)
def test_atm_brief_user_status_open_to_all_assessed_seller(atm_brief, supplier_user, case_studies, brief_assessments):
    user_status = BriefUserStatus(atm_brief, supplier_user)
    assert user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert not user_status.is_assessed_for_category()
    assert not user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert not user_status.has_been_assessed_for_brief()
    assert user_status.can_respond()
    assert not user_status.has_responded()


@pytest.mark.parametrize(
    'atm_brief',
    [{'data': atm_data}], indirect=True
)
def test_atm_brief_user_status_open_to_all_assessed_seller_responded(atm_brief, supplier_user, case_studies,
                                                                     brief_assessments, brief_response):
    user_status = BriefUserStatus(atm_brief, supplier_user)
    assert user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert not user_status.is_assessed_for_category()
    assert not user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert not user_status.has_been_assessed_for_brief()
    assert user_status.can_respond()
    assert user_status.has_responded()


@pytest.mark.parametrize(
    'atm_brief',
    [{'data': atm_data}], indirect=True
)
def test_atm_brief_user_status_open_to_all_unassessed_seller(atm_brief, supplier_user):
    user_status = BriefUserStatus(atm_brief, supplier_user)
    assert user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert not user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert not user_status.is_assessed_for_category()
    assert not user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert not user_status.has_been_assessed_for_brief()
    assert not user_status.can_respond()
    assert not user_status.has_responded()


atm_data_category = copy.copy(atm_data)
atm_data_category['openTo'] = 'category'
atm_data_category['sellerCategory'] = '1'


@pytest.mark.parametrize(
    'atm_brief',
    [{'data': atm_data_category}], indirect=True
)
def test_atm_brief_user_status_open_to_category_assessed_seller(atm_brief, supplier_user, case_studies,
                                                                brief_assessments):
    user_status = BriefUserStatus(atm_brief, supplier_user)
    assert user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert user_status.is_assessed_for_category()
    assert not user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert not user_status.has_been_assessed_for_brief()
    assert user_status.can_respond()
    assert not user_status.has_responded()


@pytest.mark.parametrize(
    'atm_brief',
    [{'data': atm_data_category}], indirect=True
)
def test_atm_brief_user_status_open_to_category_assessed_seller_responded(atm_brief, supplier_user, case_studies,
                                                                          brief_assessments, brief_response):
    user_status = BriefUserStatus(atm_brief, supplier_user)
    assert user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert user_status.is_assessed_for_category()
    assert not user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert not user_status.has_been_assessed_for_brief()
    assert user_status.can_respond()
    assert user_status.has_responded()


@pytest.mark.parametrize(
    'atm_brief',
    [{'data': atm_data_category}], indirect=True
)
def test_atm_brief_user_status_open_to_category_unassessed_seller(atm_brief, supplier_user):
    user_status = BriefUserStatus(atm_brief, supplier_user)
    assert user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert not user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert not user_status.is_assessed_for_category()
    assert not user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert not user_status.has_been_assessed_for_brief()
    assert not user_status.can_respond()
    assert not user_status.has_responded()


@pytest.mark.parametrize(
    'atm_brief',
    [{'data': atm_data_category}], indirect=True
)
@pytest.mark.parametrize(
    'supplier_domains',
    [{'status': 'unassessed', 'price_status': 'unassessed'}], indirect=True
)
def test_atm_brief_user_status_open_to_category_waiting_domain_seller(atm_brief, supplier_user, supplier_domains,
                                                                      case_studies, brief_assessments, evidence):
    user_status = BriefUserStatus(atm_brief, supplier_user)
    assert user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert not user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert not user_status.is_assessed_for_category()
    assert user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert not user_status.has_been_assessed_for_brief()
    assert not user_status.can_respond()
    assert not user_status.has_responded()


@pytest.mark.parametrize(
    'atm_brief',
    [{'data': atm_data_category}], indirect=True
)
@pytest.mark.parametrize(
    'supplier_domains',
    [{'status': 'rejected', 'price_status': 'rejected'}], indirect=True
)
def test_atm_brief_user_status_open_to_category_rejected_domain_seller(atm_brief, supplier_user, supplier_domains,
                                                                       case_studies, brief_assessments):
    atm_brief.publish()
    user_status = BriefUserStatus(atm_brief, supplier_user)
    assert user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert not user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert not user_status.is_assessed_for_category()
    assert not user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert user_status.has_been_assessed_for_brief()
    assert not user_status.can_respond()
    assert not user_status.has_responded()


def test_atm_brief_user_status_as_applicant(atm_brief, applicant_user, supplier_domains,
                                            case_studies, brief_assessments):
    user_status = BriefUserStatus(atm_brief, applicant_user)
    assert not user_status.is_approved_seller()
    assert not user_status.is_recruiter_only()
    assert not user_status.is_assessed_in_any_category()
    assert not user_status.has_evidence_in_draft_for_category()
    assert not user_status.is_assessed_for_category()
    assert not user_status.is_awaiting_domain_assessment()
    assert not user_status.is_awaiting_application_assessment()
    assert not user_status.has_been_assessed_for_brief()
    assert not user_status.can_respond()
    assert not user_status.has_responded()


@pytest.mark.parametrize('atm_brief', [{'data': atm_data}], indirect=True)
def test_can_not_respond_to_open_to_all_atm_as_recruiter(atm_brief, supplier_user):
    atm_brief.data['openTo'] = 'all'
    supplier_user.supplier.data['recruiter'] = 'yes'

    user_status = BriefUserStatus(atm_brief, supplier_user)
    result = user_status.can_respond_to_atm_opportunity()

    assert result is False


@pytest.mark.parametrize('atm_brief', [{'data': atm_data}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_respond_to_open_to_all_atm_as_assessed(atm_brief, recruiter, supplier_user, supplier_domains):
    atm_brief.data['openTo'] = 'all'
    supplier_user.supplier.data['recruiter'] = recruiter

    user_status = BriefUserStatus(atm_brief, supplier_user)
    result = user_status.can_respond_to_atm_opportunity()

    assert result is True


@pytest.mark.parametrize('atm_brief', [{'data': atm_data}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_not_respond_to_open_to_all_atm_as_unassessed(atm_brief, recruiter, supplier_user):
    atm_brief.data['openTo'] = 'all'
    supplier_user.supplier.data['recruiter'] = recruiter

    user_status = BriefUserStatus(atm_brief, supplier_user)
    result = user_status.can_respond_to_atm_opportunity()

    assert result is False


@pytest.mark.parametrize('atm_brief', [{'data': atm_data}], indirect=True)
def test_can_not_respond_to_open_to_category_atm_as_recruiter(atm_brief, supplier_user):
    atm_brief.data['openTo'] = 'category'
    supplier_user.supplier.data['recruiter'] = 'yes'

    user_status = BriefUserStatus(atm_brief, supplier_user)
    result = user_status.can_respond_to_atm_opportunity()

    assert result is False


@pytest.mark.parametrize('atm_brief', [{'data': atm_data}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_respond_to_open_to_category_atm_as_assessed(atm_brief, recruiter, supplier_user, supplier_domains):
    atm_brief.data['openTo'] = 'category'
    atm_brief.data['sellerCategory'] = '1'
    supplier_user.supplier.data['recruiter'] = recruiter

    user_status = BriefUserStatus(atm_brief, supplier_user)
    result = user_status.can_respond_to_atm_opportunity()

    assert result is True


@pytest.mark.parametrize('atm_brief', [{'data': atm_data}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_not_respond_to_open_to_category_atm_as_unassessed(atm_brief, recruiter, supplier_user, supplier_domains):
    atm_brief.data['openTo'] = 'category'
    atm_brief.data['sellerCategory'] = '1'
    supplier_user.supplier.data['recruiter'] = recruiter
    supplier_domain = next(
        supplier_domain for supplier_domain in supplier_domains if supplier_domain.domain_id == 1
    )
    supplier_domain.status = 'unassessed'

    user_status = BriefUserStatus(atm_brief, supplier_user)
    result = user_status.can_respond_to_atm_opportunity()

    assert result is False


@pytest.mark.parametrize('rfx_brief', [{'data': rfx_data}], indirect=True)
def test_can_not_respond_to_rfx_as_recruiter(rfx_brief, supplier_user):
    supplier_user.supplier.data['recruiter'] = 'yes'

    user_status = BriefUserStatus(rfx_brief, supplier_user)
    result = user_status.can_respond_to_rfx_or_training_opportunity()

    assert result is False


@pytest.mark.parametrize('rfx_brief', [{'data': rfx_data}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_respond_to_rfx_as_assessed_invited_seller(rfx_brief, recruiter, supplier_user, supplier_domains):
    supplier_user.supplier.data['recruiter'] = recruiter

    user_status = BriefUserStatus(rfx_brief, supplier_user)
    result = user_status.can_respond_to_rfx_or_training_opportunity()

    assert result is True


@pytest.mark.parametrize('rfx_brief', [{'data': rfx_data_not_selected}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_not_respond_to_rfx_as_assessed_seller_not_invited(rfx_brief, recruiter, supplier_user, supplier_domains):
    supplier_user.supplier.data['recruiter'] = recruiter

    user_status = BriefUserStatus(rfx_brief, supplier_user)
    result = user_status.can_respond_to_rfx_or_training_opportunity()

    assert result is False


@pytest.mark.parametrize('rfx_brief', [{'data': rfx_data}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_not_respond_to_rfx_as_unassessed_seller(rfx_brief, recruiter, supplier_user):
    supplier_user.supplier.data['recruiter'] = recruiter

    user_status = BriefUserStatus(rfx_brief, supplier_user)
    result = user_status.can_respond_to_rfx_or_training_opportunity()

    assert result is False


@pytest.mark.parametrize('specialist_brief', [{'data': specialist_data}], indirect=True)
def test_can_respond_to_open_to_all_specialist_as_recruiter(specialist_brief, supplier_user):
    specialist_brief.data['openTo'] = 'all'
    supplier_user.supplier.data['recruiter'] = 'yes'

    user_status = BriefUserStatus(specialist_brief, supplier_user)
    result = user_status.can_respond_to_specialist_opportunity()

    assert result is True


@pytest.mark.parametrize('specialist_brief', [{'data': specialist_data}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_respond_to_open_to_all_specialist_as_assessed(specialist_brief, recruiter, supplier_user, supplier_domains):
    specialist_brief.data['openTo'] = 'all'
    supplier_user.supplier.data['recruiter'] = recruiter

    user_status = BriefUserStatus(specialist_brief, supplier_user)
    result = user_status.can_respond_to_specialist_opportunity()

    assert result is True


@pytest.mark.parametrize('specialist_brief', [{'data': specialist_data}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_not_respond_to_open_to_all_specialist_as_unassessed(specialist_brief, recruiter, supplier_user):
    specialist_brief.data['openTo'] = 'all'
    supplier_user.supplier.data['recruiter'] = recruiter

    user_status = BriefUserStatus(specialist_brief, supplier_user)
    result = user_status.can_respond_to_specialist_opportunity()

    assert result is False


@pytest.mark.parametrize('specialist_brief', [{'data': open_to_selected_specialist_data}], indirect=True)
def test_can_respond_to_open_to_selected_specialist_as_invited_recruiter(specialist_brief, supplier_user):
    supplier_user.supplier.data['recruiter'] = 'yes'

    user_status = BriefUserStatus(specialist_brief, supplier_user)
    result = user_status.can_respond_to_specialist_opportunity()

    assert result is True


@pytest.mark.parametrize('specialist_brief', [{'data': open_to_selected_specialist_data_not_invited}], indirect=True)
def test_can_respond_to_open_to_selected_specialist_as_recruiter_not_invited(specialist_brief, supplier_user):
    supplier_user.supplier.data['recruiter'] = 'yes'

    user_status = BriefUserStatus(specialist_brief, supplier_user)
    result = user_status.can_respond_to_specialist_opportunity()

    assert result is False


@pytest.mark.parametrize('specialist_brief', [{'data': open_to_selected_specialist_data}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_respond_to_open_to_selected_specialist_as_assessed_invited_seller(specialist_brief, recruiter, supplier_user, supplier_domains):
    supplier_user.supplier.data['recruiter'] = recruiter

    user_status = BriefUserStatus(specialist_brief, supplier_user)
    result = user_status.can_respond_to_specialist_opportunity()

    assert result is True


@pytest.mark.parametrize('specialist_brief', [{'data': open_to_selected_specialist_data_not_invited}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_not_respond_to_open_to_selected_specialist_as_assessed_seller_not_invited(specialist_brief, recruiter, supplier_user, supplier_domains):
    supplier_user.supplier.data['recruiter'] = recruiter

    user_status = BriefUserStatus(specialist_brief, supplier_user)
    result = user_status.can_respond_to_specialist_opportunity()

    assert result is False


@pytest.mark.parametrize('specialist_brief', [{'data': open_to_selected_specialist_data}], indirect=True)
@pytest.mark.parametrize('recruiter', ['both', 'no'])
def test_can_not_respond_to_open_to_selected_specialist_as_unassessed_seller(specialist_brief, recruiter, supplier_user):
    supplier_user.supplier.data['recruiter'] = recruiter

    user_status = BriefUserStatus(specialist_brief, supplier_user)
    result = user_status.can_respond_to_specialist_opportunity()

    assert result is False
