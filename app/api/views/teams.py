import rollbar
from flask import jsonify
from flask_login import current_user, login_required

from app.api import api
from app.api.helpers import not_found, role_required
from app.api.services import (AuditTypes, audit_service, team_members, teams,
                              users)

from ...utils import get_json_from_request


@api.route('/team', methods=['POST'])
@login_required
@role_required('buyer')
def create_team():
    try:
        user = users.get(current_user.id)
        team = teams.create_team(user)
        team_members.set_team_lead(team_id=team.id, user_id=user.id)
    except Exception as e:
        rollbar.report_exc_info()
        return jsonify(message=e.message), 400

    try:
        audit_service.log_audit_event(
            audit_type=AuditTypes.create_team,
            db_object=team,
            user=current_user.email_address
        )
    except Exception as e:
        rollbar.report_exc_info()

    return jsonify(team.serialize())


@api.route('/team/<int:team_id>', methods=["GET"])
@login_required
@role_required('buyer')
def get_team(team_id):
    team = teams.find(id=team_id).one_or_none()
    if not team:
        not_found("No team with id '%s' found" % (team_id))

    return jsonify(team.serialize())


@api.route('/team/update', methods=['POST'])
@login_required
@role_required('buyer')
def update_team():
    data = get_json_from_request()
    return jsonify(data)
