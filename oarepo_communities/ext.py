from .permissions import permissions_cache


class OArepoCommunities(object):
    """Invenio extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["oarepo-communities"] = self


    def init_config(self, app):
        self.permissions_cache = permissions_cache

