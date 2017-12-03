import rollbar
from dmutils.csrf import check_valid_csrf
from dmutils.user import User as LoginUser
from flask import Blueprint, request, abort, current_app
from flask_login import LoginManager
from app.models import User
from base64 import b64decode
from app import encryption

auth = Blueprint('auth', __name__)
login_manager = LoginManager()


@auth.record_once
def on_load(state):
    login_manager.init_app(state.app)


@login_manager.user_loader
def load_user(userid):
    user = User.query.get(int(userid))

    if user is not None:
        user = LoginUser(user.id, user.email_address, user.supplier_code, None, user.locked,
                         user.active, user.name, user.role, user.terms_accepted_at, user.application_id)
    return user


@auth.before_request
def check_csrf_token():
    if request.method in ('POST', 'PATCH', 'PUT', 'DELETE'):
        new_csrf_valid = check_valid_csrf()

        if not (new_csrf_valid):
            rollbar.report_message('csrf.invalid_token: Aborting request check_csrf_token()', 'error', request)
            abort(400, 'Invalid CSRF token. Please try again.')


@login_manager.request_loader
def load_user_from_request(request):
    if not current_app.config.get('BASIC_AUTH'):
        return None

    payload = get_token_from_headers(request.headers)

    if payload is None:
        return None

    email_address, password = b64decode(payload).split(':', 1)
    user = User.get_by_email_address(email_address.lower())

    if user is not None:
        if encryption.authenticate_user(password, user):
            user = LoginUser(user.id, user.email_address, user.supplier_code, None, user.locked,
                             user.active, user.name, user.role, user.terms_accepted_at, user.application_id)
            return user

from app.auth.views import briefs, users, feedback, suppliers, services, prices, regions, tokens  # noqa


def get_token_from_headers(headers):
    print headers
    auth_header = headers.get('Authorization', '')
    if auth_header[:6] != 'Basic ':
        return None
    return auth_header[6:]
