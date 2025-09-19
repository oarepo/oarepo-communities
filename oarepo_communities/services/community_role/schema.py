#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from invenio_communities.communities.schema import CommunitySchema
from marshmallow import Schema, fields


#
# The default record schema
#
class CommunityRoleSchema(Schema):
    community = fields.Nested(CommunitySchema)
    role = fields.Str()
    id = fields.Str()
