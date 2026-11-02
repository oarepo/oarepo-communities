# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Schema for a community-role record."""

from __future__ import annotations

from invenio_communities.communities.schema import CommunitySchema
from marshmallow import Schema, fields


#
# The default record schema
#
class CommunityRoleSchema(Schema):
    """Schema for a community-role record."""

    community = fields.Nested(CommunitySchema)
    role = fields.Str()
    id = fields.Str()
