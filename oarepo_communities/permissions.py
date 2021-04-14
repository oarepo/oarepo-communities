# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""

#
# Action needs
#
from flask_principal import UserNeed, RoleNeed
from invenio_access import SystemRoleNeed, Permission, ParameterizedActionNeed
from invenio_records import Record
from invenio_records_rest.utils import deny_all
from oarepo_fsm.permissions import require_any, require_all, state_required

from oarepo_communities.api import OARepoCommunity
from oarepo_communities.constants import COMMUNITY_READ, COMMUNITY_CREATE, COMMUNITY_DELETE, \
    STATE_EDITING, STATE_PENDING_APPROVAL, COMMUNITY_REQUEST_CHANGES, COMMUNITY_APPROVE, \
    STATE_APPROVED, COMMUNITY_REVERT_APPROVE, COMMUNITY_PUBLISH, STATE_PUBLISHED, \
    COMMUNITY_UNPUBLISH, COMMUNITY_UPDATE, \
    COMMUNITY_REQUEST_APPROVAL
from oarepo_communities.proxies import current_oarepo_communities
from oarepo_communities.utils import community_id_from_request

community_record_owner = SystemRoleNeed('community-record-owner')


def require_action_allowed(action):
    """
    Permission factory that requires the action to be allowed by configuration.

    You can use
    ```
        require_all(require_action_allowed(COMMUNITY_CREATE), Permission(RoleNeed('editor')))
    ```
    """

    def factory(record=None, *_args, **_kwargs):
        def can():
            return action in current_oarepo_communities.allowed_actions

        return type('ActionAllowedPermission', (), {'can': can})

    return factory


def action_permission_factory(action):
    """Community action permission factory.

    Grants access to the record if the action is
    allowed and user is allowed to invoke the action in a record's PRIMARY community.

    :param action: The required community action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """

    def inner(record, *args, **kwargs):
        if record is None:
            raise RuntimeError('Record is missing.')

        arg = None
        if isinstance(record, Record):
            arg = record.primary_community
        elif isinstance(record, dict):
            arg = current_oarepo_communities.get_primary_community_field(record)
        else:
            raise RuntimeError('Unknown or missing object')
        return require_all(
            require_action_allowed(action),
            Permission(ParameterizedActionNeed(action, arg)))

    return inner


def owner_permission_factory(action, record, *args, **kwargs):
    """Owner permission factory.

    Permission factory that requires user to be the owner of the
    accessed record.

    If the record is not owned by any user, access to the record is denied.

    :param action: The required community action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """
    return owner_permission_impl


def community_role_permission_factory(role):
    """Community role permission factory.

       Permission is granted if the user belongs to a given community role.

       Usage:
       ```
            community_role_permission_factory('member')
       ```

       :param role: Community role name without community prefix.
    """

    def inner(record, *args, **kwargs):
        community_id = community_id_from_request()

        if community_id:
            community = OARepoCommunity.get_community(community_id)
            return Permission(RoleNeed(OARepoCommunity.get_role(community, role).name))
        return deny_all()

    return inner


def community_member_permission_impl(record, *args, **kwargs):
    return community_role_permission_factory('member')(record, *args, **kwargs)


def community_curator_permission_impl(record, *args, **kwargs):
    return community_role_permission_factory('curator')(record, *args, **kwargs)


def community_publisher_permission_impl(record, *args, **kwargs):
    return community_role_permission_factory('publisher')(record, *args, **kwargs)


def owner_permission_impl(record, *args, **kwargs):
    f"""Record owner permission factory.

       * Allows access to record if current_user if record is owned by the current user.
       * If the record is not owned by any user, access to the record is denied.
    """
    owners = current_oarepo_communities.get_owned_by_field(record)
    if owners:
        return Permission(
            *[UserNeed(int(owner)) for owner in owners],
        )
    return deny_all()


def owner_or_role_action_permission_factory(action, record, *args, **kwargs):
    f"""Record owner/role permission factory.

        Allows access to record if:
        * The record is owned by the current user.
        /OR/
        * User's role is allowed the required action for the record
    """
    return require_any(
        action_permission_factory(action)(record, *args, **kwargs),
        owner_permission_factory(action, record, *args, **kwargs)
    )(record, *args, **kwargs)


def read_permission_factory(record, *args, **kwargs):
    f"""Read permission factory that takes secondary communities into account.

    Allows access to record in one of the following cases:
        * Record is PUBLISHED
        * Current user is the OWNER of the record
        * User's role has allowed READ action in one of record's communities AND:
            1) User is in one of the roles of the community from the request path AND record is atleast APPROVED. OR
            2) User is CURATOR in the community from the request path

    :param record: An instance of :class:`oarepo_communities.record.CommunityRecordMixin`
        or ``None`` if the action is global.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """
    if isinstance(record, Record):
        communities = [record.primary_community, *record.secondary_communities]
        return require_any(
            #: Anyone can read published records
            state_required(STATE_PUBLISHED),
            require_all(
                require_action_allowed(COMMUNITY_READ),
                require_any(
                    #: Record AUTHOR can READ his own records
                    owner_permission_impl,
                    require_all(
                        #: User's role has granted READ permissions in record's communities
                        Permission(*[ParameterizedActionNeed(COMMUNITY_READ, x) for x in communities]),
                        require_any(
                            #: Community MEMBERS can READ APPROVED community records
                            require_all(
                                state_required(STATE_APPROVED),
                                require_any(
                                    community_member_permission_impl,
                                    community_publisher_permission_impl
                                )
                            ),
                            #: Community CURATORS can READ ALL community records
                            community_curator_permission_impl
                        )
                    )
                )
            )
        )(record, *args, **kwargs)
    else:
        raise RuntimeError('Unknown or missing object')


def create_permission_factory(record, community_id=None, *args, **kwargs):
    """Records REST create permission factory."""
    community_id = community_id or community_id_from_request()
    return Permission(ParameterizedActionNeed(COMMUNITY_CREATE, community_id))


def update_permission_factory(record, *args, **kwargs):
    f"""Records REST update permission factory.

       Permission is granted if:
       * Record is a DRAFT AND
         * Current user is the OWNER of the record and record is not submitted for APPROVAL yet. OR
         * Current user is in role that has UPDATE action allowed in record's PRIMARY community.
    """
    return require_all(
        state_required(None, STATE_EDITING, STATE_PENDING_APPROVAL),
        require_any(
            require_all(
                state_required(None, STATE_EDITING),
                owner_permission_impl
            ),
            action_permission_factory(COMMUNITY_UPDATE)(record, *args, **kwargs)
        )

    )(record, *args, **kwargs)


def delete_permission_factory(record, *args, **kwargs):
    """Records REST delete permission factory."""
    return owner_or_role_action_permission_factory(COMMUNITY_DELETE, record, *args, **kwargs)


def request_approval_permission_factory(record, *args, **kwargs):
    f"""Request approval action permissions factory.

       Permission is granted if:
       * Record an EDITED DRAFT record. AND
         * Current user is the owner of the record. OR
         * Current user is in role that has REQUEST APPROVAL action allowed
           in record's PRIMARY community.
    """
    return require_all(
        state_required(None, STATE_EDITING),
        owner_or_role_action_permission_factory(COMMUNITY_REQUEST_APPROVAL, record)
    )(record, *args, **kwargs)


def delete_draft_permission_factory(record, *args, **kwargs):
    f"""Delete DRAFT records permissions factory.

       Permission is granted if:
       * Record is a DRAFT record AND
         * Current user is the owner of the record. OR
         * Current user is in role that has DELETE action allowed in record's PRIMARY community.
    """
    return require_all(
        state_required(None, STATE_EDITING, STATE_PENDING_APPROVAL),
        owner_or_role_action_permission_factory(COMMUNITY_DELETE, record)
    )(record, *args, **kwargs)


def request_changes_permission_factory(record, *args, **kwargs):
    f"""Request changes action permissions factory.

       Permission is granted if:
       * Record is submitted for approval. AND
       * Current user is in role that has REQUEST CHANGES action allowed in record's PRIMARY community.
    """
    return require_all(
        state_required(STATE_PENDING_APPROVAL),
        action_permission_factory(COMMUNITY_REQUEST_CHANGES)(record, *args, **kwargs)
    )(record, *args, **kwargs)


def approve_permission_factory(record, *args, **kwargs):
    f"""Approve action permissions factory.

       Permission is granted if:
       * Record is submitted for approval. AND
       * Current user is in role that has APPROVE action allowed in record's PRIMARY community.
    """
    return require_all(
        state_required(STATE_PENDING_APPROVAL),
        action_permission_factory(COMMUNITY_APPROVE)(record, *args, **kwargs)
    )(record, *args, **kwargs)


def revert_approval_permission_factory(record, *args, **kwargs):
    f"""Revert approval action permissions factory.

       Permission is granted if:
       * Record is APPROVED. AND
       * Current user is in role that has REVERT APPROVE action allowed in record's PRIMARY community.
    """
    return require_all(
        state_required(STATE_APPROVED),
        action_permission_factory(COMMUNITY_REVERT_APPROVE)(record, *args, **kwargs)
    )(record, *args, **kwargs)


def publish_permission_factory(record, *args, **kwargs):
    f"""Publish action permissions factory.

       Permission is granted if:
       * Record is APPROVED. AND
       * Current user is in role that has PUBLISH action allowed in record's PRIMARY community.
    """
    return require_all(
        state_required(STATE_APPROVED),
        action_permission_factory(COMMUNITY_PUBLISH)(record, *args, **kwargs)
    )(record, *args, **kwargs)


def unpublish_permission_factory(record, *args, **kwargs):
    f"""Unpublish action permissions factory.

       Permission is granted if:
       * Record is PUBLISHED. AND
       * Current user is in role that has UNPUBLISH action allowed in record's PRIMARY community.
    """
    return require_all(
        state_required(STATE_PUBLISHED),
        action_permission_factory(COMMUNITY_UNPUBLISH)(record, *args, **kwargs)
    )(record, *args, **kwargs)


# REST endpoints permission factories.
read_object_permission_impl = read_permission_factory

create_object_permission_impl = create_permission_factory

update_object_permission_impl = update_permission_factory

delete_object_permission_impl = delete_permission_factory

# Record actions permission factories.
request_approval_permission_impl = request_approval_permission_factory

delete_draft_permission_impl = delete_draft_permission_factory

request_changes_permission_impl = request_changes_permission_factory

approve_permission_impl = approve_permission_factory

revert_approval_permission_impl = revert_approval_permission_factory

publish_permission_impl = publish_permission_factory

unpublish_permission_impl = unpublish_permission_factory
