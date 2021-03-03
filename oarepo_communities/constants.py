# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""

COMMUNITY_READ = 'community-read'
"""Action needed: read/list records in a community."""

COMMUNITY_CREATE = 'community-create'
"""Action needed: create a record in a community."""

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