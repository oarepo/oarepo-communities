# OARepo communities

## Installation

To init custom fields, add them under COMMUNITIES_CUSTOM_FIELDS key to invenio.cfg,
for example

```python
from oarepo_communities.cf.permissions import PermissionsCF
from oarepo_communities.cf.aai import AAIMappingCF

COMMUNITIES_CUSTOM_FIELDS = [PermissionsCF("permissions"), AAIMappingCF("aai")]
COMMUNITIES_CUSTOM_FIELDS_UI = [{
     "section": "settings",
     "fields": [{
                 "field": "permissions",
                 "ui_widget": "Input",
                 "props": {
                             "label":"permissions dict",
                          }
                }]
 }]
```

and the init cli command:
invenio communities custom-fields init
