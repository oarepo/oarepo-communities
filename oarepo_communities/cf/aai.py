import marshmallow
from invenio_records_resources.services.custom_fields import BaseCF
from marshmallow import fields as ma_fields


class AAIMappingSchema(marshmallow.Schema):
    aai_group = ma_fields.String()
    role = ma_fields.String()


class AAIMappingCF(BaseCF):
    @property
    def mapping(self):
        return {
            "type": "object",
            "properties": {
                "aai_group": {"type": "keyword"},
                "role": {"type": "keyword"},
            },
        }

    @property
    def field(self):
        return ma_fields.List(ma_fields.Nested(AAIMappingSchema))
        # example {
        #          "owner":   {"can_create": true ,  "can_read": true, "can_update": true ,  "can_delete":true },
        #          "manager": {"can_create": true ,  "can_read": true, "can_update": true ,  "can_delete":true },
        #          "curator": {"can_create": true ,  "can_read": true, "can_update": true ,  "can_delete":false},
        #          "reader":  {"can_create": false,  "can_read": true, "can_update": false,  "can_delete":false},
        #          }

    # cf = [{"role": "curator", "aai_group": "urn:geant:cesnet.cz:group:VO_nrp_development:test_community:curator#perun.cesnet.cz"}]
