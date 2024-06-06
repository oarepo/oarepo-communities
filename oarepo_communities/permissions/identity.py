from flask_principal import Identity
from invenio_access.permissions import SystemRoleNeed

request_active = SystemRoleNeed("request")


class RequestIdentity(Identity):
    def __init__(self, identity):
        super().__init__(identity.id, identity.auth_type)
        self.provides = identity.provides | {request_active}
