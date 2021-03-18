# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from invenio_records_rest.schemas.fields import SanitizedUnicode
from marshmallow import Schema
from marshmallow.fields import List


class OARepoCommunitiesMixin(Schema):
    _primary_community = SanitizedUnicode(required=True)
    _communities = List(SanitizedUnicode, default=list)
