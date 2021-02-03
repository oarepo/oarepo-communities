# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CESNET.
#
# OARepo-Communities is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""OArepo module that adds support for communities"""
import flask
from flask import current_app
from werkzeug.local import LocalProxy

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


def create_test_role(role, **kwargs):
    """Create a role in the datastore.

    Accesses the application's datastore. An error is thrown if called from
    outside of an application context.

    Returns the created user model object instance, with the plaintext password
    as `user.password_plaintext`.

    :param name: The name of the role.
    :returns: A :class:`invenio_accounts.models.Role` instance.
    """
    assert flask.current_app.testing
    role = _datastore.create_role(name=role, **kwargs)
    _datastore.commit()
    return role
