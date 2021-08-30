
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
    "oarepo:primaryCommunity":{
        "type": "string"
    },
    "oarepo:secondaryCommunities": {
        "type": "array",
        "items": {
            "type": "string"
        }
    },
    "oarepo:recordStatus": {
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

or if you want you can use your custom schema and you have to specify JSON address separated by dots (level1.level2
etc.) in configuration. Please see example:
```python
OAREPO_COMMUNITIES_PRIMARY_COMMUNITY_FIELD = 'address1.separated.by.dots'
OAREPO_COMMUNITIES_OWNED_BY_FIELD = 'address2.separated.by.dots'
OAREPO_COMMUNITIES_COMMUNITIES_FIELD = 'address3.separated.by.dots'
```

## Installation

OARepo-Communities is on PyPI so all you need is:

``` console
$ pip install oarepo-communities
```

## Configuration

### Community record class

To use this module, you need to inherit your Record class from the following mixin.
You should also implement `canonical_url` with `CommunityPIDValue` for record's `pid_value`,
which provides an ID of record's primary community e.g.:
```python
from oarepo_communities.record import CommunityRecordMixin

class CommunityRecord(CommunityRecordMixin, Record):
...
@property
def canonical_url(self):
    return url_for(f'invenio_records_rest.records/record_item',
                   pid_value=CommunityPIDValue(
                       self['id'],
                       current_oarepo_communities.get_primary_community_field(self)
                   ), _external=True)
```

### Community Roles
To customize invenio roles to be created inside each community, override the following defaults:
```python
OAREPO_COMMUNITIES_ROLES = ['member', 'curator', 'publisher']
"""Roles present in each community."""
```

This configuration will create an internal Invenio roles named:
```
community:<community_id>:member
community:<community_id>:curator
community:<community_id>:publisher
```

for each newly created community.

### Community actions

Community action grants users having community roles associated with the action a permission to
perform a certain action on all records in the community (given that other necessary conditions
are also met, e.g. record's ownership and/or current state, see [Permissions](https://github.com/oarepo/oarepo-communities#permissions)).

To customize which actions could be assigned to community roles, override the following defaults:
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

### Default role actions permission matrix

You can customize default action permissions assigned to roles of newly
created communities by customizing:

```python
OAREPO_COMMUNITIES_DEFAULT_ACTIONS = {
   'any': [], # e.g. anonymous, non-community users
   'author': [], # owners of the records
   'member': [COMMUNITY_CREATE],
   'curator': [COMMUNITY_READ, COMMUNITY_APPROVE, COMMUNITY_UPDATE, COMMUNITY_REQUEST_CHANGES, COMMUNITY_DELETE],
   'publisher': [COMMUNITY_PUBLISH, COMMUNITY_REVERT_APPROVE]
}
"""Default action2role permission matrix for newly created communities."""
```

### REST Endpoints
Register Records REST endpoints that will represent community record collections under:
```python
OAREPO_COMMUNITIES_ENDPOINTS = ['recid', ...]
"""List of community enabled endpoints."""

OAREPO_FSM_ENABLED_REST_ENDPOINTS = ['recid', ...]
"""Enable FSM transitions for the community record collection."""
```
_NOTE: items should be the keys of `RECORDS_REST_ENDPOINTS` config dict._

Endpoints registered as community endpoints are expected to have item and list paths in the
following format:
```python
RECORDS_REST_ENDPOINTS={
    list_route=f'/<community_id>/',
    item_route=f'/<commpid({pid_type},record_class="{record_class}"):pid_value>',
...
}
```

#### Links Factory

For this library to work, you will need to set the following links factory in your `RECORDS_REST_ENDPOINTS`:
```python
from oarepo_communities.links import community_record_links_factory
...
RECORDS_REST_ENDPOINTS={
    'recid': {
        ...
        links_factory_imp=partial(community_record_links_factory, original_links_factory=your_original_links_factory),
    }
```
***WARNING***: `your_original_links_factory` should expect `CommunityPIDValue` instance to be passed for link
generation as record's `pid_value`

## Search

To limit search results to records in a certain community, use the following in your `RECORDS_REST_ENDPOINTS`:

```python
from oarepo_communities.search import CommunitySearch, community_search_factory
...
RECORDS_REST_ENDPOINTS={
    'recid': {
        ...
        search_class=CommunitySearch,
        search_factory_imp=community_search_factory
    }
```

This will restrict the results of a search query to just the records having primary or secondary
community ID obtained from the current request. Further
filtering will occur considering the current user community roles and records state
(see [Permissions](https://github.com/oarepo/oarepo-communities#permissions)).

If the community ID could not be determined from the current request, results will be
filtered with all IDs of communities where the current user is in any role.

## Permissions

This library provides the permission factories to be used for securing `RECORDS_REST_ENDPOINTS` community-enabled
collections. It also provides default permissions for each community action.

Default community permission factories together with default `OAREPO_COMMUNITIES_DEFAULT_ACTIONS` config implements the following
permissions matrix in a collection of community records:

### State-based permissions

Each role is granted permissions based on a state of the record:

| state | anonymous/any | author |  member  | curator | publisher | admin |
|------|-------------|-------|-----------|---------|--------|---------|
| filling |       x            |   r/w    |         c        |      r/w     |       x     |       r/w     |
| approving |     x      |   r        |        x         |      r/w     |     x       |       r/w     |
| approved  |     x      |   r        |        r          |       r       |      r       |       r/w                    |
| published |     r      |    r       |        r          |       r       |      r        |        r(+unpublish) |


_r(read), w(update), c(create)_

### Action need permissions

Each role is granted community-scope restricted permissions to invoke a certain actions on a record.

| role | actions |
|-----|-------|
| author | request-approval (own records only) |
| curator | approve, delete, read, request-changes, update |
| publisher | publish, revert-approve |
| admin | all above + unpublish |

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
Usage: oarepo oarepo:communities create [OPTIONS] COMMUNITY_ID TITLE

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
Usage: oarepo oarepo:communities actions [OPTIONS] COMMAND [ARGS]...

  Management commands for OARepo Communities actions.

Options:
  --help  Show this message and exit.

Commands:
  allow  Allow actions to the given role.
  deny   Deny actions on the given role.
  list   List all available community actions.
```

#### Discover available communities

```shell
$ oarepo oarepo:communities list
- cesnet - CESNET community A testing CESNET community to test oarepo-communities
```

#### Discover actions available/assigned to the community roles

```yaml
$ oarepo oarepo:communities actions list -c cesnet
Available actions:
- read
- create
- update
- request-approval
- approve
- revert-approve
- request-changes
- delete
- publish
- unpublish

Available community roles:
- author
- any
- publisher
- curator
- member

Allowed community role actions:
- create: publisher, curator
- publish: publisher
- read: publisher
- request-changes: curator

Allowed system role actions:
```

#### Allow a certain actions for the certain community role

```shell
$ oarepo oarepo:communities actions allow cesnet curator delete approve revert-approve
Added role action: community-delete Need(method='role', value='community:cesnet:curator')
Added role action: community-approve Need(method='role', value='community:cesnet:curator')
Added role action: community-revert-approve Need(method='role', value='community:cesnet:curator')

```

### REST API

This library registers the folowing REST API routes for OARepo:

#### Community list

```shell
curl http://127.0.0.1:5000/communities/
 {
    'comtest': {
        'id': 'comtest',
        'metadata': {'description': 'Community description'},
        'title': 'Title',
        'type': 'Other',
        'links': {
            'self': 'https://localhost/communities/comtest'
        }
    }},
    ...
 }
```

#### Community Detail

```shell
community_id=comtest
curl http://127.0.0.1:5000/communities/${community_id}
{
    'id': 'comtest',
    'metadata': {'description': 'Community description'},
    'title': 'Title',
    'type': 'Other',
    'actions': { # present for community members only
       'community-read': ['community:comtest:curator', 'community-record-owner'],
       'community-update': ['community-record-owner'],
       ...
     },
    'links': {
        'self': 'https://localhost/communities/comtest'
    }
}}
```

Further documentation is available on
https://oarepo-communities.readthedocs.io/

Copyright (C) 2021 CESNET.

OARepo-Communities is free software; you can redistribute it and/or
modify it under the terms of the MIT License; see LICENSE file for more
details.
