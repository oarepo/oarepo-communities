# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OARepo-Communities views."""
import json
from collections import defaultdict

from flask import Blueprint, jsonify, Response, abort

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.links import community_links_factory
from oarepo_communities.models import OARepoCommunityModel
from oarepo_communities.permissions import community_member_permission_impl


def json_abort(status_code, detail):
    resp = Response(json.dumps(detail, indent=4, ensure_ascii=False),
                    status=status_code,
                    mimetype='application/json; charset=utf-8')
    abort(status_code, response=resp)


blueprint = Blueprint(
    'oarepo_communities',
    __name__,
    url_prefix='/communities'
)


@blueprint.route('/')
def community_list():
    """Community list view."""
    comms = OARepoCommunityModel.query.all()
    return jsonify([{
        **comm.to_json(),
        'links': community_links_factory(comm)
    } for comm in comms])


@blueprint.route('/<community_id>', strict_slashes=False)
def community_detail(community_id):
    """Community list view."""
    comm = OARepoCommunity.get_community(community_id)
    if comm:
        ars, sars = comm.actions
        actions = defaultdict(list)

        if community_member_permission_impl(None).can():
            alist = ars + sars
            # Community member can list action permission matrix
            for act in alist:
                for action, roles in act.items():
                    actions[action] += [r.need.value for r in roles]

        return jsonify({
            **comm.to_json(),
            'links': community_links_factory(comm),
            **({'actions': actions} if actions else {})
        })
    json_abort(404, {
        "message": "community %s was not found" % community_id
    })
