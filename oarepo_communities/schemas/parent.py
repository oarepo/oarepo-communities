from oarepo_runtime.services.schema.ui import LocalizedDateTime
from marshmallow import Schema, fields
from invenio_rdm_records.services.schemas.parent.communities import CommunitiesSchema
from marshmallow.fields import Field
from invenio_communities.communities.records.api import Community


class CommunityField(Field):
    def _deserialize(self, value: str | Community, attr: str, data, **kwargs) -> Community:
        if not isinstance(value, Community):
            return Community.pid.resolve(value)
        return value

    def _serialize(self, value: Community | None, attr: str, obj, **kwargs) -> str | None:
        if value is None:
            return None
        return str(value.id)

class CommunitiesParentSchema(
    CommunitiesSchema
):
    default = CommunityField()

class CommunityUISchema(Schema):
    created = LocalizedDateTime(dump_only=True)
    updated = LocalizedDateTime(dump_only=True)

    def dump(self, obj, **kwargs):
        """Overriding marshmallow dump"""
        dumped = super().dump(obj, **kwargs)
        return obj | dumped

class CommunitiesParentUISchema(
    Schema
):
    entries = fields.List(fields.Nested(CommunityUISchema))
    def dump(self, obj, **kwargs):
        """Overriding marshmallow dump"""
        dumped = super().dump(obj, **kwargs)
        return obj | dumped

