# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""


class OARepoCommunityCreateError(Exception):
    """Failed to create community error."""

    def __init__(self, community, *args, **kwargs):
        """Constructor.

        :param schema: path of the requested schema which was not found.
        """
        self.community = community
        super(OARepoCommunityCreateError, self).__init__(
            'Failed to create community "{}"'.format(community), *args, **kwargs
        )
