# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask_login import current_user
from invenio_records_rest.schemas.fields import SanitizedUnicode
from marshmallow import Schema, pre_load
from marshmallow.fields import List, Integer


class OARepoCommunitiesMixin(Schema):
    # TODO: use current_communities to get field names from app config
    _primary_community = SanitizedUnicode(required=True,
                                          data_key='oarepo:primaryCommunity',
                                          attribute='oarepo:primaryCommunity')
    _secondary_communities = List(SanitizedUnicode, default=list,
                                  data_key='oarepo:secondaryCommunities',
                                  attribute='oarepo:secondaryCommunities')
    _owned_by = Integer(data_key='oarepo:ownedBy', attribute='oarepo:ownedBy')

    @pre_load
    def set_oarepo_submitter(self, data, **kwargs):
        """Set oarepo:submitter to record metadata if not known."""
        if not data.get('oarepo:ownedBy'):
            if current_user and current_user.is_authenticated:
                data['oarepo:ownedBy'] = current_user.id
            else:
                data['oarepo:ownedBy'] = None
        return data
