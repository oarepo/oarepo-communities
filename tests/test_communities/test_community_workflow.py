#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from invenio_communities.communities.records.api import Community
from oarepo_rdm.oai.percolator import init_percolators
from invenio_communities.proxies import current_communities


def test_change_workflow(
    logged_client,
    communities_model,
    community_owner,
    community,
    search_clear,
):
    init_percolators() # TODO: automate?
    owner_client = logged_client(community_owner)
    community_item = current_communities.service.read(community_owner.identity, community.id)

    result = owner_client.put(
        f"/communities/{community.id}",
        json= community_item.data | {"custom_fields": {"workflow": "doesnotexist"}},
    )
    assert result.status_code == 400
    result = owner_client.put(
        f"/communities/{community.id}",
        json= community_item.data | {"custom_fields": {"workflow": "custom"}},
    )
    assert result.status_code == 200
    community_id = str(community.id)
    record = Community.get_record(community_id)
    assert record.custom_fields["workflow"] == "custom"
