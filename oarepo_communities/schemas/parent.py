from marshmallow import Schema, fields


class CommunitiesParentSchema(
    Schema
):  # todo consider using invenio_rdm_records.services.schemas.parent.communities
    ids = fields.List(fields.String())
    default = fields.String()
