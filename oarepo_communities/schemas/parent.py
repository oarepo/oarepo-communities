#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from marshmallow import Schema, fields


class CommunitiesParentSchema(Schema):  # TODO consider using invenio_rdm_records.services.schemas.parent.communities
    ids = fields.List(fields.String())
    default = fields.String()
