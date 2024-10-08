from flask import current_app
from werkzeug.local import LocalProxy

current_oarepo_communities = LocalProxy(
    lambda: current_app.extensions["oarepo-communities"]
)
