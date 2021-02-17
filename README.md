
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

## Installation

OARepo-Communities is on PyPI so all you need is:

``` console
$ pip install oarepo-communities
```

## Configuration

To customize invenio roles to be created inside each community, override the following defaults:
```python
OAREPO_COMMUNITIES_ROLES = ['member', 'curator', 'publisher']
"""Roles present in each community."""
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

Further documentation is available on
https://oarepo-communities.readthedocs.io/

Copyright (C) 2021 CESNET.

OARepo-Communities is free software; you can redistribute it and/or
modify it under the terms of the MIT License; see LICENSE file for more
details.
