import json
import pytest

from app import encryption
from app.models import db, utcnow, Supplier, SupplierFramework, Contact, SupplierDomain, User,\
    Framework, UserFramework, AuditEvent
from faker import Faker
from dmapiclient.audit import AuditTypes
from datetime import date
import pendulum

fake = Faker()


@pytest.fixture()
def suppliers(app, request):
    with app.app_context():
        for i in range(1, 6):
            db.session.add(Supplier(
                abn=i,
                code=(i),
                name='Test Supplier{}'.format(i),
                contacts=[Contact(name='auth rep', email='auth@rep.com')],
                data={'contact_email': 'test{}@supplier.com'.format(i)}
            ))

            db.session.flush()

        framework = Framework.query.filter(Framework.slug == "digital-marketplace").first()
        db.session.add(SupplierFramework(supplier_code=1, framework_id=framework.id))

        db.session.commit()
        yield Supplier.query.all()


@pytest.fixture()
def supplier_domains(app, request, suppliers):
    with app.app_context():
        for s in suppliers:
            for i in range(1, 6):
                db.session.add(SupplierDomain(
                    supplier_id=s.id,
                    domain_id=i,
                    status='assessed'
                ))

                db.session.flush()

        db.session.commit()
        yield SupplierDomain.query.all()


@pytest.fixture()
def supplier_user(app, request, suppliers):
    with app.app_context():
        db.session.add(User(
            id=100,
            email_address='j@examplecompany.biz',
            name=fake.name(),
            password=encryption.hashpw('testpassword'),
            active=True,
            role='supplier',
            supplier_code=suppliers[0].code,
            password_changed_at=utcnow()
        ))
        db.session.commit()
        db.session.flush()
        framework = Framework.query.filter(Framework.slug == "digital-outcomes-and-specialists").first()
        db.session.add(UserFramework(user_id=100, framework_id=framework.id))
        db.session.commit()
        yield User.query.first()


def test_create_new_brief_response(client, supplier_user, supplier_domains, briefs, assessments, suppliers):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.post(
        '/2/brief/1/respond',
        data=json.dumps({
            'essentialRequirements': ['ABC', 'XYZ'],
            'availability': '01/01/2018',
            'respondToEmailAddress': 'supplier@email.com',
            'specialistName': 'Test Specialist Name',
            'dayRate': '100',
        }),
        content_type='application/json'
    )
    assert res.status_code == 201


def test_create_brief_response_creates_an_audit_event(client, supplier_user, supplier_domains,
                                                      briefs, assessments, suppliers):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.post(
        '/2/brief/1/respond',
        data=json.dumps({
            'essentialRequirements': ['ABC', 'XYZ'],
            'availability': '01/01/2018',
            'respondToEmailAddress': 'supplier@email.com',
            'specialistName': 'Test Specialist Name',
            'dayRate': '100',
        }),
        content_type='application/json'
    )
    assert res.status_code == 201

    audit_events = AuditEvent.query.filter(
        AuditEvent.type == AuditTypes.create_brief_response.value
    ).all()

    assert len(audit_events) == 1
    assert audit_events[0].data['briefResponseId'] == 1


def test_create_brief_response_with_object(client, supplier_user,
                                           supplier_domains, briefs,
                                           assessments, suppliers):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.post(
        '/2/brief/1/respond',
        data=json.dumps({
            'essentialRequirements': {'0': 'ABC', '1': 'XYZ'},
            'availability': '01/01/2018',
            'respondToEmailAddress': 'supplier@email.com',
            'specialistName': 'Test Specialist Name',
            'dayRate': '100',
        }),
        content_type='application/json'
    )
    assert res.status_code == 201


def test_cannot_respond_to_a_brief_more_than_three_times_from_the_same_supplier(client, supplier_user,
                                                                                supplier_domains, briefs,
                                                                                assessments, suppliers):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    for i in range(0, 3):
        res = client.post(
            '/2/brief/1/respond',
            data=json.dumps({
                'essentialRequirements': ['ABC', 'XYZ'],
                'availability': '01/01/2018',
                'respondToEmailAddress': 'supplier@email.com',
                'specialistName': 'Test Specialist Name',
                'dayRate': '100',
            }),
            content_type='application/json'
        )
        assert res.status_code == 201

    res = client.post(
        '/2/brief/1/respond',
        data=json.dumps({
            'essentialRequirements': ['ABC', 'XYZ'],
            'availability': '01/01/2018',
            'respondToEmailAddress': 'supplier@email.com',
            'specialistName': 'Test Specialist Name',
            'dayRate': '100',
        }),
        content_type='application/json'
    )
    assert res.status_code == 400
    assert 'There are already 3 brief responses for supplier' in res.get_data(as_text=True)


def test_cannot_respond_to_a_brief_with_wrong_number_of_essential_reqs(client, supplier_user,
                                                                       supplier_domains, briefs,
                                                                       assessments, suppliers):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.post(
        '/2/brief/1/respond',
        data=json.dumps({
            'essentialRequirements': ['XYZ'],
            'availability': '01/01/2018',
            'respondToEmailAddress': 'supplier@email.com',
            'specialistName': 'Test Specialist Name',
            'dayRate': '100',
        }),
        content_type='application/json'
    )
    assert res.status_code == 400
    assert 'Essential requirements must be completed' in res.get_data(as_text=True)


def test_create_brief_response_success_with_audit_exception(client, supplier_user, supplier_domains,
                                                            briefs, assessments, suppliers, mocker):
    audit_event = mocker.patch('app.api.views.briefs.audit_service')
    audit_event.side_effect = Exception('Test')

    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.post(
        '/2/brief/1/respond',
        data=json.dumps({
            'essentialRequirements': ['ABC', 'XYZ'],
            'availability': '01/01/2018',
            'respondToEmailAddress': 'supplier@email.com',
            'specialistName': 'Test Specialist Name',
            'dayRate': '100',
        }),
        content_type='application/json'
    )
    assert res.status_code == 201


def test_get_brief(client, supplier_user, supplier_domains, briefs, assessments, suppliers):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.post(
        '/2/brief/1/respond',
        data=json.dumps({
            'essentialRequirements': ['ABC', 'XYZ'],
            'availability': '01/01/2018',
            'respondToEmailAddress': 'supplier@email.com',
            'specialistName': 'Test Specialist Name',
            'dayRate': '100',
        }),
        content_type='application/json'
    )
    assert res.status_code == 201

    res = client.get(
        '/2/brief/1',
        content_type='application/json'
    )
    data = json.loads(res.get_data(as_text=True))
    assert res.status_code == 200
    assert data['id'] == 1


@pytest.mark.parametrize(
    'briefs',
    [{'published_at': '%s-01-01' % (date.today().year - 1), 'closed_at': '%s-01-07' % (date.today().year - 1)}],
    indirect=True
)
def test_get_brief_sellers_success(client, supplier_user, supplier_domains, briefs, assessments, suppliers,
                                   brief_responses):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'test@digital.gov.au', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.get(
        '/2/brief/1/sellers',
        content_type='application/json'
    )
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert data['sellers'][0]['supplier_code'] == 1
    assert data['sellers'][0]['supplier_name'] == 'Test Supplier1'


@pytest.mark.parametrize(
    'briefs',
    [{'published_at': '%s-01-01' % (date.today().year - 1), 'closed_at': '%s-01-07' % (date.today().year - 1)}],
    indirect=True
)
def test_get_brief_sellers_success_no_responses(client, supplier_user, supplier_domains, briefs, assessments,
                                                suppliers):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'test@digital.gov.au', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.get(
        '/2/brief/1/sellers',
        content_type='application/json'
    )
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert len(data['sellers']) == 0


def test_get_brief_sellers_failure_current_user_not_buyer(client, supplier_user, supplier_domains, briefs, assessments,
                                                          suppliers, brief_responses):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.get(
        '/2/brief/1/sellers',
        content_type='application/json'
    )
    assert res.status_code == 403


@pytest.mark.parametrize(
    'briefs',
    [{'closed_at': pendulum.now().add(days=7).to_datetime_string()}],
    indirect=True
)
def test_get_brief_sellers_failure_not_yet_closed(client, supplier_user, supplier_domains, briefs, assessments,
                                                  suppliers, brief_responses):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'test@digital.gov.au', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.get(
        '/2/brief/1/sellers',
        content_type='application/json'
    )
    assert res.status_code == 403


def test_send_brief_sellers_notify_success(client, supplier_user, supplier_domains, briefs, assessments, suppliers,
                                           brief_responses, mocker):
    send_seller_email = mocker.patch('app.api.views.briefs.send_seller_email')
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'test@digital.gov.au', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.post(
        '/2/brief/1/sellers/notify',
        data=json.dumps({
            'subject': 'test subject',
            'content': 'test content',
            'selectedSellers': [{
                'supplier_name': 'Test Supplier1',
                'supplier_code': '1',
                'contact_name': 'Test Name'
            }]
        }),
        content_type='application/json'
    )
    assert res.status_code == 204
    assert send_seller_email.called


def test_send_brief_sellers_notify_failure_missing_input(client, supplier_user, supplier_domains, briefs, assessments,
                                                         suppliers, brief_responses, mocker):
    send_seller_email = mocker.patch('app.api.views.briefs.send_seller_email')
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'test@digital.gov.au', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.post(
        '/2/brief/1/sellers/notify',
        data=json.dumps({
            'subject': 'test subject',
            'selectedSellers': [{
                'supplier_name': 'Test Supplier1',
                'supplier_code': '1',
                'contact_name': 'Test Name'
            }]
        }),
        content_type='application/json'
    )
    assert res.status_code == 400
    assert not send_seller_email.called


def test_send_brief_sellers_notify_failure_empty_sellers(client, supplier_user, supplier_domains, briefs, assessments,
                                                         suppliers, brief_responses, mocker):
    send_seller_email = mocker.patch('app.api.views.briefs.send_seller_email')
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'test@digital.gov.au', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.post(
        '/2/brief/1/sellers/notify',
        data=json.dumps({
            'subject': 'test subject',
            'content': 'test content',
            'selectedSellers': []
        }),
        content_type='application/json'
    )
    assert res.status_code == 400
    assert not send_seller_email.called


def test_send_brief_sellers_notify_failure_invalid_sellers(client, supplier_user, supplier_domains, briefs,
                                                           assessments, suppliers, brief_responses, mocker):
    send_seller_email = mocker.patch('app.api.views.briefs.send_seller_email')
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'test@digital.gov.au', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.post(
        '/2/brief/1/sellers/notify',
        data=json.dumps({
            'subject': 'test subject',
            'content': 'test content',
            'selectedSellers': [{
                'supplier_name': 'Test Supplier999',
                'supplier_code': '999',
                'contact_name': 'Test Name'
            }]
        }),
        content_type='application/json'
    )
    assert res.status_code == 400
    assert not send_seller_email.called
