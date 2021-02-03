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
