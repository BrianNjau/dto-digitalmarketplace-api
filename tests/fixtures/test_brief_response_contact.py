import json
import pytest

from app import encryption
from app.models import db, utcnow, Supplier, SupplierFramework, Contact, SupplierDomain, User,\
    Framework, UserFramework, AuditEvent
from faker import Faker
from dmapiclient.audit import AuditTypes

fake = Faker()


@pytest.fixture()
def suppliers(app, request):
    with app.app_context():
        for i in range(1, 6):
            db.session.add(Supplier(
                abn=i,
                code=(i),
                name='Test Supplier{}'.format(i),
                contacts=[Contact(name='auth rep', email='auth@rep.com')]
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


def test_get_brief_response_contact(client, supplier_user, supplier_domains, briefs, assessments, suppliers):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    for i in range(1, 3):
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
        '/2/brief-response-contact/{}'.format(1),
        content_type='application/json'
    )
    data = json.loads(res.get_data(as_text=True))
    assert res.status_code == 200
    assert data['briefId'] == 1
    assert data['supplierCode'] == 1
    assert data['emailAddress'] == 'j@examplecompany.biz'


def test_get_brief_response_contact_not_found(client, supplier_user, supplier_domains, briefs, assessments, suppliers):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.get(
        '/2/brief-response-contact/{}'.format(1),
        content_type='application/json'
    )
    data = json.loads(res.get_data(as_text=True))
    assert res.status_code == 404
    assert data['message'] == 'Cannot find brief response contact with brief_id :1 and supplier_code: 1'


def test_save_brief_response_contact(client, supplier_user, supplier_domains, briefs, assessments, suppliers):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    for i in range(1, 3):
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

    res = client.put(
        '/2/brief-response-contact/{}'.format(1),
        data=json.dumps({
            'emailAddress': 'test@a.com'
        }),
        content_type='application/json'
    )
    assert res.status_code == 200
    data = json.loads(res.get_data(as_text=True))
    assert data['emailAddress'] == 'test@a.com'

    res = client.get(
        '/2/brief-response-contact/{}'.format(1),
        content_type='application/json'
    )
    data = json.loads(res.get_data(as_text=True))
    assert res.status_code == 200
    assert data['briefId'] == 1
    assert data['supplierCode'] == 1
    assert data['emailAddress'] == 'test@a.com'


def test_save_brief_response_contact_not_found(client, supplier_user, supplier_domains, briefs, assessments, suppliers):
    res = client.post('/2/login', data=json.dumps({
        'emailAddress': 'j@examplecompany.biz', 'password': 'testpassword'
    }), content_type='application/json')
    assert res.status_code == 200

    res = client.put(
        '/2/brief-response-contact/{}'.format(1),
        data=json.dumps({
            'emailAddress': 'test@a.com'
        }),
        content_type='application/json'
    )
    assert res.status_code == 404
    data = json.loads(res.get_data(as_text=True))
    assert data['message'] == 'Cannot find brief response contact with brief_id :1 and supplier_code: 1'
