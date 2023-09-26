from flask import current_app
from werkzeug.local import LocalProxy

current_communities_permissions = LocalProxy(lambda: current_app.extensions["oarepo-communities"].permissions_cache)