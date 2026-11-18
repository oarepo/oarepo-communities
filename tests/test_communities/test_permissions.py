# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest
from flask_principal import Identity, UserNeed
from invenio_access.permissions import system_identity
from invenio_communities.communities.records.api import Community
from invenio_communities.generators import CommunityRoleNeed
from invenio_communities.proxies import current_communities
from invenio_records_resources.services.errors import PermissionDeniedError
from invenio_search.engine import dsl
from oarepo_rdm.oai.percolator import init_percolators
from oarepo_runtime.typing import record_from_result
from oarepo_workflows import Workflow, WorkflowRequestPolicy
from pytest_oarepo.communities.functions import set_community_workflow

from oarepo_communities.requests.utils import user_has_permission
from oarepo_communities.services.permissions.generators import (
    CommunitiesAwareInAnyWorkflow,
    DefaultCommunityRole,
    IfNoRecordOrData,
    InAnyCommunity,
    InAnyContextCommunity,
    RecordOwnerInRecordCommunity,
)
from oarepo_communities.services.permissions.policy import CommunityDefaultWorkflowPermissions


def test_disabled_endpoints(
    logged_client,
    community_owner,
    draft_with_community_submission_factory,
    published_record_with_community_factory,
    default_record_with_workflow_json,
    community_get_or_create_in_default_workflow,
    record_service,
    urls,
    search_clear,
):
    owner_client = logged_client(community_owner)
    community_1 = community_get_or_create_in_default_workflow(community_owner, "comm1")
    draft = draft_with_community_submission_factory(community_owner.identity, str(community_1.id))
    published_record = published_record_with_community_factory(community_owner.identity, str(community_1.id))
    publish = owner_client.post(f"{urls['BASE_URL']}/{draft['id']}/draft/actions/publish")
    delete = owner_client.delete(f"{urls['BASE_URL']}/{published_record['id']}")
    assert publish.status_code == 403
    assert delete.status_code == 403


def test_default_community_workflow_changed(
    community_owner,
    users,
    community_get_or_create_in_default_workflow,
    draft_with_community_submission_factory,
    submit_review,
    invite,
    search_clear,
):
    init_percolators()
    community_reader = users[0]
    community_1 = community_get_or_create_in_default_workflow(community_owner, "comm1")
    community_2 = community_get_or_create_in_default_workflow(community_owner, "comm2")
    invite(community_reader, str(community_1.id), "reader")
    invite(community_reader, str(community_2.id), "reader")

    draft_before_change = draft_with_community_submission_factory(community_reader.identity, str(community_1.id))

    set_community_workflow(str(community_1.id), "no")
    assert Community.get_record(str(community_1.id)).custom_fields["workflow"] == "no"

    # the review takes the new workflow of the community, which does not allow community submissions
    with pytest.raises(PermissionDeniedError):
        draft_with_community_submission_factory(community_reader.identity, str(community_1.id))

    draft_other_community = draft_with_community_submission_factory(community_reader.identity, str(community_2.id))

    assert draft_before_change["parent"]["workflow"] == "default"
    assert draft_other_community["parent"]["workflow"] == "default"
    submit_review(community_reader.identity, draft_before_change["id"])
    submit_review(community_reader.identity, draft_other_community["id"])


def _record_owners_in_record_community_test(
    community_owner,
    users,
    logged_client,
    draft_with_community_submission_factory,
    record_service,
    community_get_or_create,
    workflow,
    urls,
    results,
) -> None:
    # tries to read record when user in record's primary community, in noth primary and secondary, in secondary and
    # in none
    community_curator = users[0]
    community_1 = community_get_or_create(community_owner, "comm1")
    community_2 = community_get_or_create(community_owner, "comm2")
    community_3 = community_get_or_create(community_curator, "comm3")

    owner_client = logged_client(community_owner)

    record = draft_with_community_submission_factory(
        community_owner.identity,
        str(community_1.id),
        custom_workflow=workflow,
    )
    record_id = record["id"]

    # the draft enters its community only when its review is accepted, which also publishes it,
    # so the draft communities are set directly
    record = record_from_result(record_service.read_draft(system_identity, record_id))
    record.parent.communities.add(community_1, default=True)
    record.parent.commit()

    read_com1 = owner_client.get(f"{urls['BASE_URL']}/{record_id}/draft?expand=true")

    record = record_from_result(record_service.read_draft(system_identity, record_id))
    record.parent.communities.add(community_2, default=False)
    record.parent.commit()

    read_com2 = owner_client.get(f"{urls['BASE_URL']}/{record_id}/draft?expand=true")

    record = record_from_result(record_service.read_draft(system_identity, record_id))
    record.parent.communities.remove(community_1)
    record.parent.communities.add(community_3, default=True)
    record.parent.commit()

    read_com3 = owner_client.get(f"{urls['BASE_URL']}/{record_id}/draft?expand=true")

    record = record_from_result(record_service.read_draft(system_identity, record_id))
    record.parent.communities.remove(community_2)
    record.parent.commit()

    read_com4 = owner_client.get(f"{urls['BASE_URL']}/{record_id}/draft?expand=true")

    assert read_com1.status_code == results[0]
    assert read_com2.status_code == results[1]
    assert read_com3.status_code == results[2]
    assert read_com4.status_code == results[3]


def test_record_owners_in_record_community_needs(
    community_owner,
    urls,
    users,
    logged_client,
    community_get_or_create_in_default_workflow,
    draft_with_community_submission_factory,
    record_service,
    search_clear,
) -> None:
    _record_owners_in_record_community_test(
        community_owner,
        users,
        logged_client,
        draft_with_community_submission_factory,
        record_service,
        community_get_or_create_in_default_workflow,
        workflow="record_owner_in_record_community",
        urls=urls,
        results=(200, 200, 200, 403),
    )


def test_record_owners_in_default_record_community_needs(
    community_owner,
    urls,
    users,
    logged_client,
    community_get_or_create_in_default_workflow,
    draft_with_community_submission_factory,
    record_service,
    search_clear,
) -> None:
    _record_owners_in_record_community_test(
        community_owner,
        users,
        logged_client,
        draft_with_community_submission_factory,
        record_service,
        community_get_or_create_in_default_workflow,
        workflow="record_owner_in_default_record_community",
        urls=urls,
        results=(200, 200, 403, 403),
    )


def test_in_any_community(
    community_owner,
    community_get_or_create_in_default_workflow,
    search_clear,
):
    community_1 = community_get_or_create_in_default_workflow(community_owner, "comm1")
    community_2 = community_get_or_create_in_default_workflow(community_owner, "comm2")

    generator = InAnyCommunity(DefaultCommunityRole("owner"))
    needs = generator.needs()

    expected = {
        CommunityRoleNeed(str(community_1.id), "owner"),
        CommunityRoleNeed(str(community_2.id), "owner"),
    }
    assert expected.issubset(set(needs))


def test_can_submit_in_community_without_explicit_allowed_workflows(
    communities_model, community_owner, minimal_community
):
    communities_service = current_communities.service
    community = record_from_result(communities_service.create(community_owner.identity, minimal_community))
    assert communities_service.check_permission(community_owner.identity, "submit_record", record=community)


def test_record_owner_in_record_community_searches_owned_records_in_member_communities(app):
    identity = Identity(1)
    identity.provides |= {UserNeed(1), CommunityRoleNeed("comm-id", "reader")}

    query = RecordOwnerInRecordCommunity().query_filter(identity=identity)

    assert query == dsl.Q("terms", **{"parent.access.owned_by.user": [1]}) & dsl.Q(
        "terms", **{"parent.communities.ids": ["comm-id"]}
    )


def test_record_owner_in_record_community_searches_nothing_without_membership(app):
    identity = Identity(1)
    identity.provides.add(UserNeed(1))

    assert RecordOwnerInRecordCommunity().query_filter(identity=identity) == dsl.Q("match_none")


def test_create_needs_contain_owner_role_of_each_community_allowing_the_workflow(
    community_owner,
    community_get_or_create_in_default_workflow,
    search_clear,
):
    community_1 = community_get_or_create_in_default_workflow(community_owner, "comm1")
    community_2 = community_get_or_create_in_default_workflow(community_owner, "comm2")

    generator = CommunitiesAwareInAnyWorkflow("create")
    needs = generator.needs()

    expected = {
        CommunityRoleNeed(str(community_1.id), "owner"),
        CommunityRoleNeed(str(community_2.id), "owner"),
    }
    assert expected.issubset(set(needs))


def test_owner_can_create_in_community_when_workflow_policy_is_evaluated_directly(
    community_owner,
    community_get_or_create_in_default_workflow,
    search_clear,
):
    # used by the migration request; evaluates the workflow's can_create without CommunitiesAwareInAnyWorkflow
    community = community_get_or_create_in_default_workflow(community_owner, "direct-wf-check")

    assert user_has_permission(community_owner.identity, community, "create")


def test_manage_files_is_granted_by_role_in_record_community_not_in_any_community(
    community_owner,
    users,
    invite,
    community_get_or_create_in_default_workflow,
    published_record_with_community_factory,
    record_service,
    search_clear,
):
    # default workflow: can_manage_files = SameAs("can_create"); with a record, IfNewRecord takes the else_ branch
    record_community = community_get_or_create_in_default_workflow(community_owner, "record-community")
    other_community = community_get_or_create_in_default_workflow(community_owner, "other-community")
    other_community_owner = users[0]
    invite(other_community_owner, str(other_community.id), "owner")

    record_id = published_record_with_community_factory(community_owner.identity, str(record_community.id))["id"]
    record = record_from_result(record_service.read(system_identity, record_id))

    assert record_service.check_permission(community_owner.identity, "manage_files", record=record)
    assert not record_service.check_permission(other_community_owner.identity, "manage_files", record=record)


class CuratorCreatesPermissions(CommunityDefaultWorkflowPermissions):
    """Curators of communities allowing this workflow can create."""

    can_create = (
        IfNoRecordOrData(
            then_=[InAnyContextCommunity(DefaultCommunityRole("curator"))],
            else_=[DefaultCommunityRole("curator")],
        ),
    )


class OwnerCreatesPermissions(CommunityDefaultWorkflowPermissions):
    """Owners of communities allowing this workflow can create."""

    can_create = (
        IfNoRecordOrData(
            then_=[InAnyContextCommunity(DefaultCommunityRole("owner"))],
            else_=[DefaultCommunityRole("owner")],
        ),
    )


def test_curator_cannot_create_through_workflow_not_allowed_in_their_community(
    app,
    monkeypatch,
    community_owner,
    users,
    invite,
    community_get_or_create,
    record_service,
    search_clear,
):
    workflows = [
        Workflow(
            code="curator_creates",
            label="Curators create",
            permission_policy_cls=CuratorCreatesPermissions,
            request_policy_cls=WorkflowRequestPolicy,
        ),
        Workflow(
            code="owner_creates",
            label="Owners create",
            permission_policy_cls=OwnerCreatesPermissions,
            request_policy_cls=WorkflowRequestPolicy,
        ),
    ]
    # cached_property read by the community custom field validation; patch it before WORKFLOWS,
    # otherwise monkeypatch would compute (and later restore) it from the patched config
    monkeypatch.setattr(app.extensions["oarepo-workflows"], "workflow_by_code", {w.code: w for w in workflows})
    monkeypatch.setitem(app.config, "WORKFLOWS", workflows)

    community = community_get_or_create(
        community_owner, "owners-only", workflow="owner_creates", allowed_workflows=["owner_creates"]
    )
    curator = users[0]
    invite(curator, str(community.id), "curator")

    assert record_service.check_permission(community_owner.identity, "create")
    assert not record_service.check_permission(curator.identity, "create")
