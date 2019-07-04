import rollbar
from flask import jsonify, request
from flask_login import current_user, login_required

from app.api import api
from app.api.business import team_business
from app.api.business.errors import TeamError
from app.api.helpers import abort, get_email_domain, not_found, role_required
from app.api.services import (AuditTypes, audit_service, team_members, teams,
                              users)
from app.models import Team

from ...utils import get_json_from_request


@api.route('/teams', methods=['GET'])
@login_required
@role_required('buyer')
def get_team_overview():
    team = team_business.get_team_overview()

    return jsonify(team)


@api.route('/team/create', methods=['POST'])
@login_required
@role_required('buyer')
def create_team():
    try:
        team = team_business.create_team()
    except TeamError as e:
        abort(e.message)
    except Exception as e:
        rollbar.report_exc_info()

    return jsonify(team)


@api.route('/team/<int:team_id>', methods=["GET"])
@login_required
@role_required('buyer')
def get_team(team_id):
    team = team_business.get_team(team_id)

    return jsonify(team)


@api.route('/team/<int:team_id>/update', methods=['POST'])
@login_required
@role_required('buyer')
def update_team(team_id):
    data = get_json_from_request()
    team = team_business.update_team(data)

    return jsonify(team)


@api.route('/team/members/search', methods=['GET'])
@login_required
@role_required('buyer')
def find_team_members():
    keywords = request.args.get('keywords') or ''
    if keywords:
        results = users.get_team_members(
            current_user.id,
            get_email_domain(current_user.email_address),
            keywords=keywords
        )

        return jsonify(users=results), 200
    else:
        abort('You must provide a keywords param.')
