from invenio_records_resources.services.custom_fields import BaseCF
from marshmallow import fields as ma_fields


class PermissionsCF(BaseCF):
    """"""

    @property
    def mapping(self):
        return {"type": "object", "dynamic": True}

    @property
    def mapping_settings(self):
        return {}

    @property
    def field(self):
        return ma_fields.Dict(
            keys=ma_fields.String,
            values=ma_fields.Dict(keys=ma_fields.String, values=ma_fields.Boolean),
        )
        # example {
        #          "owner":   {"can_create": true ,  "can_read": true, "can_update": true ,  "can_delete":true },
        #          "manager": {"can_create": true ,  "can_read": true, "can_update": true ,  "can_delete":true },
        #          "curator": {"can_create": true ,  "can_read": true, "can_update": true ,  "can_delete":false},
        #          "reader":  {"can_create": false,  "can_read": true, "can_update": false,  "can_delete":false},
        #          }
