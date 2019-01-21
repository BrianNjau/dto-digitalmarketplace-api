from app.api.helpers import Service
from app.models import Domain
from app import db
from six import string_types
from sqlalchemy import func
from sqlalchemy.orm import joinedload


class DomainService(Service):
    __model__ = Domain

    def __init__(self, *args, **kwargs):
        super(DomainService, self).__init__(*args, **kwargs)

    def get_by_name_or_id(self, name_or_id):
        if isinstance(name_or_id, string_types):
            domain = self.filter(
                func.lower(Domain.name) == func.lower(name_or_id)
            ).one_or_none()
        else:
            domain = self.get(name_or_id).one_or_none()

        return domain

    def get_domain_with_criterias(self, name_or_id):
        query = (
            db
            .session
            .query(Domain)
            .options(
                joinedload(Domain.domain_criterias)
            )
        )
        if isinstance(name_or_id, string_types):
            query = query.filter(
                func.lower(Domain.name) == func.lower(name_or_id)
            )
        else:
            query = query.filter(Domain.id == name_or_id)

        result = query.one_or_none()
        if result:
            return {
                "id": result.id,
                "name": result.name,
                "price_minimum": result.price_minimum,
                "price_maximum": result.price_maximum,
                "domain_criterias": [{
                    "id": r.id,
                    "name": r.name
                } for r in result.domain_criterias]
            }
        else:
            return None
