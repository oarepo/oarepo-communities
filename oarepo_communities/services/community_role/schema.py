from invenio_communities.communities.schema import CommunitySchema
from marshmallow import Schema, fields


#
# The default record schema
#
class CommunityRoleSchema(Schema):
    community = fields.Nested(CommunitySchema)
    role = fields.Str()
    id = fields.Str()
