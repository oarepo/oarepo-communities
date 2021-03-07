# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask import request
from werkzeug.exceptions import BadRequest

from oarepo_communities.constants import PRIMARY_COMMUNITY_FIELD


def community_json_loader():
    data = request.get_json(force=True)
    rcomid = request.view_args['community_id']
    dcomid = data.get(PRIMARY_COMMUNITY_FIELD, None)
    if dcomid:
        if rcomid != dcomid:
            raise BadRequest('Primary Community mismatch')
    else:
        data[PRIMARY_COMMUNITY_FIELD] = rcomid

    return data
