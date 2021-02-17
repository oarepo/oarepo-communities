# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
from flask import current_app
from invenio_accounts.proxies import current_datastore
from invenio_db import db
from invenio_records.api import RecordBase

from oarepo_communities.errors import OARepoCommunityCreateError
from oarepo_communities.models import OARepoCommunityModel
from oarepo_communities.signals import before_community_insert, after_community_insert
from oarepo_communities.utils import community_role_kwargs, community_kwargs_from_role


class OARepoCommunity(RecordBase):
    model_cls = OARepoCommunityModel

    @classmethod
    def create(cls, data, title, ctype='other', id_=None, **kwargs):
        """Create a new Community instance and store it in the database."""
        with db.session.begin_nested():
            comm = cls(data)
            comm.model = cls.model_cls(
                id=id_,
                title=title,
                type=ctype,
                json=comm)

            before_community_insert.send(
                current_app._get_current_object(),
                community=comm.model
            )
            cls._create_community_roles(comm.model)

            db.session.add(comm.model)

        after_community_insert.send(
            current_app._get_current_object(),
            community=comm.model
        )

        return comm.model

    @classmethod
    def _create_community_roles(cls, community):
        role_kwargs_impl = current_app.config.get('OAREPO_COMMUNITIES_ROLE_NAME', community_role_kwargs)
        roles = current_app.config['OAREPO_COMMUNITIES_ROLES']

        for role in roles:
            role_kwargs = role_kwargs_impl(community, role)
            role = current_datastore.find_or_create_role(str(role_kwargs['name']))
            if not role:
                raise OARepoCommunityCreateError(community)

            role.description = role_kwargs['description']
            current_datastore.put(role)

    @classmethod
    def get_community(cls, id_, with_deleted=False, **kwargs):
        """Retrieve the community by its id.

        Raise a database exception if the community does not exist.

        :param id_: community ID.
        :param with_deleted: If `True` then it includes deleted communities.
        :returns: The :class:`OARepoCommunityModel` instance.
        """
        with db.session.no_autoflush:
            query = cls.model_cls.query.filter_by(id=id_)
            if not with_deleted:
                query = query.filter(cls.model_cls.json != None)  # noqa
            obj = query.one()
            return cls(obj.json, model=obj).model

    @classmethod
    def get_community_from_role(cls, role):
        """Retrieve the community for a given role.

        :param role: A flask Role instance
        :returns: The :class:`OARepoCommunityModel` instance,
                  None if role is not associated with any community.
        """
        kwargs = community_kwargs_from_role(role)
        if kwargs:
            return cls.get_community(**kwargs)

    @classmethod
    def get_communities(cls, ids, with_deleted=False):
        """Retrieve multiple communities by id.

        :param ids: List of community IDs.
        :param with_deleted: If `True` then it includes deleted communities.
        :returns: A list of :class:`OARepoCommunityModel` instances.
        """
        with db.session.no_autoflush:
            query = cls.model_cls.query.filter(cls.model_cls.id.in_(ids))
            if not with_deleted:
                query = query.filter(cls.model_cls.json != None)  # noqa

            return [cls(obj.json, model=obj).model for obj in query.all()]
