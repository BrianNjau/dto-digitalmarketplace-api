from flask import request, jsonify
from flask_login import login_required, current_user
from app.api import api
from app.api.business import buyer_dashboard_business
from app.api.helpers import get_email_domain, role_required


@api.route('/buyer/dashboard', methods=['GET'])
@login_required
@role_required('buyer')
def buyer_dashboard():
    """Buyer dashboard (role=buyer)
    ---
    tags:
      - dashboard
    definitions:
      BuyerDashboard:
        type: object
        properties:
            brief:
              type: object
              properties:
                code:
                  type: string
                name:
                  type: string
            messages:
              type: object
              properties:
                items:
                  $ref: '#/definitions/SellerDashboardMessageItem'
    responses:
      200:
        description: Supplier dashboard info
        schema:
          $ref: '#/definitions/SellerDashboard'

    """
    status = request.args.get('status', None)
    result = buyer_dashboard_business.get_briefs(current_user.id, status)
    counts = buyer_dashboard_business.get_brief_counts(current_user.id)

    return jsonify(
        briefs=result,
        brief_counts=counts
    ), 200
