# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask import request
from werkzeug.exceptions import BadRequest

from oarepo_communities.proxies import current_oarepo_communities
from oarepo_communities.utils import community_id_from_request


def community_json_loader():
    data = request.get_json(force=True)
    rcomid = community_id_from_request()
    dcomid = current_oarepo_communities.get_primary_community_field(data)
    if dcomid:
        if rcomid != dcomid:
            raise BadRequest('Primary Community mismatch')
    else:
        current_oarepo_communities.set_primary_community_field(data, rcomid)

    return data
