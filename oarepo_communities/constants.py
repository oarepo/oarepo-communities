# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""

# Available community actions
COMMUNITY_READ = 'community-read'
"""Action needed: read/list records in a community."""

COMMUNITY_CREATE = 'community-create'
"""Action needed: create a record in a community."""

COMMUNITY_UPDATE = 'community-update'
"""Action needed: update a record in a community."""

COMMUNITY_REQUEST_APPROVAL = 'community-request-approval'
"""Action needed: request community record approval."""

COMMUNITY_APPROVE = 'community-approve'
"""Action needed: approve community record."""

COMMUNITY_REVERT_APPROVE = 'community-revert-approve'
"""Action needed: revert community record approval."""

COMMUNITY_REQUEST_CHANGES = 'community-request-changes'
"""Action needed: request changes to community record."""

COMMUNITY_PUBLISH = 'community-publish'
"""Action needed: publish community record."""

COMMUNITY_UNPUBLISH = 'community-unpublish'
"""Action needed: unpublish community record."""

COMMUNITY_DELETE = 'community-delete'
"""Action needed: delete community draft record."""

# Available community record states
STATE_EDITING = 'editing'
"""State: record is an edited draft."""

STATE_PENDING_APPROVAL = 'pending-approval'
"""State: record creator has finished editing and submitted record for approval."""

STATE_APPROVED = 'approved'
"""State: record has been validated and approved for publishing."""

STATE_PUBLISHED = 'published'
"""State: record has been made public."""

STATE_DELETED = 'deleted'
"""State: record draft has been deleted."""
