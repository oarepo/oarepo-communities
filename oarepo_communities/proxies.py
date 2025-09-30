#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-communities (see https://github.com/oarepo/oarepo-communities).
#
# oarepo-communities is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from flask import current_app
from werkzeug.local import LocalProxy

current_oarepo_communities = LocalProxy(lambda: current_app.extensions["oarepo-communities"])
