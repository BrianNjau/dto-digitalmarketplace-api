from dmutils.data_tools import ValidationError
from dmutils.filters import timesince
from flask import jsonify, abort, current_app, request
from sqlalchemy import desc
from sqlalchemy.orm import joinedload, lazyload, noload
from sqlalchemy.exc import IntegrityError
import pendulum
from pendulum.parsing.exceptions import ParserError

from app.api.services import (
    team_service
)
from app.tasks import publish_tasks
from .. import main
from ... import db
from ...models import (
    User,
    Brief,
    TeamBrief, 
    Team
)
from ...utils import (
    get_json_from_request, get_int_or_400, json_has_required_keys, pagination_links,
    get_valid_page_or_1, get_request_page_questions, validate_and_return_updater_request,
    get_positive_int_or_400
)
from ...service_utils import validate_and_return_lot, filter_services

from ...datetime_utils import parse_time_of_day, combine_date_and_time

@main.route('/team/<int:team_id>', methods=['GET'])
def get_team(team_id):
    print(team_id)
    team = (
        Team
        .query
        .filter(
            Team.id == team_id
        )
        .first_or_404()
    )
    return jsonify(teamsId=team.id)