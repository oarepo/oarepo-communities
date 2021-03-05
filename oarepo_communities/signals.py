# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""

from blinker import Namespace

_signals = Namespace()

before_community_insert = _signals.signal('before-community-insert')
"""Signal is sent before a community is inserted.

When implementing the event listener, the community data can be retrieved from
`kwarg['community']`.
Example event listener (subscriber) implementation:

.. code-block:: python

    def listener(sender, *args, **kwargs):
        community = kwargs['community']
        # do something with the community

    from oarepo_communities.signals import before_community_insert
    before_community_insert.connect(listener)
"""

after_community_insert = _signals.signal('after-community-insert')
"""Signal sent after a community is inserted.

When implementing the event listener, the community data can be retrieved from
`kwarg['community']`.

.. note::

   Do not perform any modification to the community here: they will be not
   persisted.
"""

on_request_approval = _signals.signal('on-community-request-approve')
"""Signal sent when community record transitions to pending approval state."""

on_delete_draft = _signals.signal('on-community-delete-draft')
"""Signal sent when community record delete draft action is triggered.

   When implementing the event listener, it is your responsibility
   to commit any changes to the record.
"""

on_request_changes = _signals.signal('on-community-request-changes')
"""Signal sent when community record transitions from approved to editing state."""

on_approve = _signals.signal('on-community-approve')
"""Signal sent when community record transtions to approved state.

   When implementing the event listener, it is your responsibility
   to commit any changes to the record.
"""

on_revert_approval = _signals.signal('on-community-revert-approval')
"""Signal sent when community record transitions from approved to pending approval state.

   When implementing the event listener, it is your responsibility
   to commit any changes to the record.
"""

on_publish = _signals.signal('on-community-publish')
"""Signal sent when community record transitions from approved to published state."""

on_unpublish = _signals.signal('on-community-unpublish')
"""Signal sent when community record transitions published to approved state."""
