from flask import jsonify
from flask_login import login_required

from app.api import api
from app.api.helpers import role_required

from ...utils import get_json_from_request


@api.route('/team/update', methods=['POST'])
@login_required
@role_required('buyer')
def update_team():
    data = get_json_from_request()
    return jsonify(data)
