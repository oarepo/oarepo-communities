
[![image][0]][1]
[![image][2]][3]
[![image][4]][5]
[![image][6]][7]

  [0]: https://github.com/oarepo/oarepo-communities/workflows/CI/badge.svg
  [1]: https://github.com/oarepo/oarepo-communities/actions?query=workflow%3ACI
  [2]: https://img.shields.io/github/tag/oarepo/oarepo-communities.svg
  [3]: https://github.com/oarepo/oarepo-communities/releases
  [4]: https://img.shields.io/pypi/dm/oarepo-communities.svg
  [5]: https://pypi.python.org/pypi/oarepo-communities
  [6]: https://img.shields.io/github/license/oarepo/oarepo-communities.svg
  [7]: https://github.com/oarepo/oarepo-communities/blob/master/LICENSE

# OARepo-Communities

OArepo module that adds support for communities

## Prerequisites

To use this library, you need to configure your `RECORDS_REST_ENDPOINTS`
to use [OARepo FSM](https://github.com/oarepo/oarepo-fsm)
and [OARepo Records Draft](https://github.com/oarepo/invenio-records-draft) libraries first.

Ensure that your Record Metadata schema contains the following fields:
```json
{
    "_primary_community":{
        "type": "string"
    },
    "_communities": {
        "type": "array",
        "items": {
            "type": "string"
        }
    },
    "state": {
        "type": "string"
    },
    "access": {
        "owned_by": {
            "description": "List of user IDs that are owners of the record.",
            "type": "array",
            "minItems": 1,
            "uniqueItems": true,
            "items": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                    "user": {
                        "type": "integer"
                    }
                }
            }
        }
    }
}
```

## Installation

OARepo-Communities is on PyPI so all you need is:

``` console
$ pip install oarepo-communities
```

## Configuration

### Community record class

To use this module, you need to inherit your Record class from the following mixin:
```python
from oarepo_communities.record import CommunityRecordMixin

class CommunityRecord(CommunityRecordMixin, Record):
...
```

### Community Roles
To customize invenio roles to be created inside each community, override the following defaults:
```python
OAREPO_COMMUNITIES_ROLES = ['member', 'curator', 'publisher']
"""Roles present in each community."""
```

### Community actions
To customize, which actions should be allowed to be assigned to community roles, override the following defaults:
```python
OAREPO_COMMUNITIES_ALLOWED_ACTIONS = [
    COMMUNITY_READ, COMMUNITY_CREATE,
    COMMUNITY_REQUEST_APPROVAL, COMMUNITY_APPROVE, COMMUNITY_REVERT_APPROVE,
    COMMUNITY_REQUEST_CHANGES,
    COMMUNITY_PUBLISH,
    COMMUNITY_UNPUBLISH
]
"""Community actions available to community roles."""
```

Register Records REST endpoints that will represent community record collections under:
```python
OAREPO_COMMUNITIES_ENDPOINTS = ['recid', ...]
"""List of community enabled endpoints."""

OAREPO_FSM_ENABLED_REST_ENDPOINTS = ['recid', ...]
"""Enable FSM transitions for the community record collection."""
```

Endpoints registered as community endpoints are expected to have item and list paths in the
following format:
```python
RECORDS_REST_ENDPOINTS={
    list_route=f'/<community_id>/',
    item_route=f'/<commpid({pid_type},record_class="{record_class}"):pid_value>',
...
}
```

### Links Factory

For this library to work, you will need to set the following links factory in your `RECORDS_REST_ENDPOINTS`:
```python
from oarepo_communities.links import community_record_links_factory
...
RECORDS_REST_ENDPOINTS={
    'recid': {
        ...
        links_factory_imp=community_record_links_factory,
    }
```

### Search class

To limit search results to records in a community, use the following search class in your `RECORDS_REST_ENDPOINTS`:

```python
from oarepo_communities.search import CommunitySearch
...
RECORDS_REST_ENDPOINTS={
    'recid': {
        ...
        search_class=CommunitySearch,
    }
```

## Signals

Each community action defined on CommunityRecordMixin sends a signal whenever
a record's state changes. The
following [signals](https://github.com/oarepo/oarepo-communities/oarepo_communities/signals.py) are available for
each possible action. You will need to connect to these signals in your app to
execute any extra actions needed on each state change event.

```python
on_request_approval = _signals.signal('on-community-request-approve')
"""Signal sent when community record transitions to pending approval state."""

on_delete_draft = _signals.signal('on-community-delete-draft')
"""Signal sent when community record delete draft action is triggered.

   When implementing the event listener, it is your responsibility
   to commit any changes to the record.
"""

on_request_changes = _signals.signal('on-community-request-changes')
"""Signal sent when community record transitions from approved to editing state."""

on_approve = _signals.signal('on-community-approve')
"""Signal sent when community record transtions to approved state.

   When implementing the event listener, it is your responsibility
   to commit any changes to the record.
"""

on_revert_approval = _signals.signal('on-community-revert-approval')
"""Signal sent when community record transitions from approved to pending approval state.

   When implementing the event listener, it is your responsibility
   to commit any changes to the record.
"""

on_publish = _signals.signal('on-community-publish')
"""Signal sent when community record transitions from approved to published state."""

on_unpublish = _signals.signal('on-community-unpublish')
"""Signal sent when community record transitions published to approved state."""
```


## Usage

### CLI

You can find all CLI commands that are available under `invenio oarepo:communities` group.

To create a community, use:
````shell
Usage: invenio oarepo:communities create [OPTIONS] COMMUNITY_ID TITLE

Options:
  --description TEXT  Community description
  --policy TEXT       Curation policy
  --title TEXT        Community title
  --logo-path TEXT    Path to the community logo file
  --ctype TEXT        Type of a community
  --help              Show this message and exit.
````

This command will create a new community together with Invenio Roles for the community.
Created community roles will be defined by default as:

```python
dict(
    name=f'community:{community_id}:{community_role}',
    description=f'{title} - {community_role}'
)
```

This can be customized by using custom `OAREPO_COMMUNITIES_ROLE_KWARGS` factory.

To manage actions allowed on each role in a community use the following CLI commands:
```
Usage: invenio oarepo:communities actions [OPTIONS] COMMAND [ARGS]...

  Management commands for OARepo Communities actions.

Options:
  --help  Show this message and exit.

Commands:
  allow  Allow actions to the given role.
  deny   Deny actions on the given role.
  list   List all available community actions.
```

Further documentation is available on
https://oarepo-communities.readthedocs.io/

Copyright (C) 2021 CESNET.

OARepo-Communities is free software; you can redistribute it and/or
modify it under the terms of the MIT License; see LICENSE file for more
details.
