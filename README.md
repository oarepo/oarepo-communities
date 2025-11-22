# OARepo Communities

Community-based workflow and permission extensions for [Invenio](https://inveniosoftware.org/) framework.

## Overview

This package extends Invenio with community-centric features:

- Community-based workflow management with configurable permissions
- Advanced permission generators for community roles and members
- Service components for community inclusion and access control
- Request types for community operations (submission, migration, removal)
- Custom fields for workflow configuration at community level
- CLI commands for community and membership management
- Model presets for integrating communities into record models
- Integration with OARepo workflows and requests

## Installation

```bash
pip install oarepo-communities
```

### Requirements

- Python 3.13+
- Invenio 14.x
- oarepo-runtime>=2.0.0dev23
- oarepo-workflows>=2.0.0dev3
- oarepo-requests>=3.0.0dev1

## Key Features

### 1. Community Workflow Management

**Source:** [`oarepo_communities/workflow.py`](oarepo_communities/workflow.py), [`oarepo_communities/services/custom_fields/workflow.py`](oarepo_communities/services/custom_fields/workflow.py)

Each community can have its own default workflow, allowing different communities to enforce different approval processes and permissions for records.

#### Workflow Configuration

```python
from oarepo_workflows import Workflow
from oarepo_communities.services.permissions.policy import CommunityDefaultWorkflowPermissions

class MyWorkflowPermissions(CommunityDefaultWorkflowPermissions):
    can_read = [AnyUser()]
    can_create = [DefaultCommunityRole("owner"), DefaultCommunityRole("reader")]

# In invenio.cfg
WORKFLOWS = {
    'default': Workflow(
        code='default',
        label='Default Workflow',
        permission_policy_cls=MyWorkflowPermissions,
    )
}
```

#### Community Custom Fields

Communities can specify their default workflow and allowed workflows via custom fields:

```python
# Setting workflow on community creation
from invenio_communities.proxies import current_communities

current_communities.service.create(
    identity,
    {
        "slug": "my-community",
        "metadata": {"title": "My Community"},
        "custom_fields": {
            "workflow": "default",
            "allowed_workflows": ["default", "strict_review"]
        }
    }
)
```

#### Automatic Workflow Resolution

```python
from oarepo_communities.proxies import current_oarepo_communities

# Get workflow from community
workflow = current_oarepo_communities.get_community_default_workflow(
    data={"parent": {"communities": {"default": {"id": "community-slug"}}}}
)
```

### 2. Permission Generators

**Source:** [`oarepo_communities/services/permissions/generators.py`](oarepo_communities/services/permissions/generators.py)

Comprehensive set of permission generators for community-based access control.

#### Community Role Generators

```python
from oarepo_communities.services.permissions.generators import (
    CommunityRole,
    DefaultCommunityRole,
    CommunityMembers,
    DefaultCommunityMembers,
    TargetCommunityRole,
)

# Allow specific role in any community associated with record
CommunityRole("curator")  # Curators in any primary or secondary community

# Allow specific role only in the default (primary) community
DefaultCommunityRole("owner")  # Only owners of the primary community

# Allow any member of communities associated with record
CommunityMembers()  # Any member of any community

# Allow any member of the default community
DefaultCommunityMembers()  # Any member of primary community

# For request types - target community specified in payload
TargetCommunityRole("owner")  # Owner of the community being joined
```

#### Record Owner in Community Generators

These generators combine record ownership with community membership:

```python
from oarepo_communities.services.permissions.generators import (
    RecordOwnerInDefaultRecordCommunity,
    RecordOwnerInRecordCommunity,
)

# Owner only has access if they're a member of the record's primary community
RecordOwnerInDefaultRecordCommunity()

# Owner only has access if they're a member of any of the record's communities
RecordOwnerInRecordCommunity()
```

#### Workflow-based Permission Wrapper

```python
from oarepo_communities.services.permissions.generators import CommunityWorkflowPermission

# Automatically resolves workflow from community and applies permissions
CommunityWorkflowPermission("create")  # Uses community's default workflow
```

#### Usage Example

```python
from oarepo_communities.services.permissions.policy import (
    CommunityDefaultWorkflowPermissions,
)
from oarepo_communities.services.permissions.generators import (
    DefaultCommunityRole,
    RecordOwnerInDefaultRecordCommunity,
)
from invenio_records_permissions.generators import AnyUser
from oarepo_workflows import IfInState

class MyWorkflowPermissions(CommunityDefaultWorkflowPermissions):
    can_read = [
        RecordOwnerInDefaultRecordCommunity(),
        DefaultCommunityRole("curator"),
        IfInState("published", [AnyUser()]),
    ]
    
    can_create = [
        DefaultCommunityRole("owner"),
        DefaultCommunityRole("curator"),
    ]
    
    can_update = [
        IfInState("draft", [RecordOwnerInDefaultRecordCommunity()]),
        IfInState("published", [DefaultCommunityRole("owner")]),
    ]
```

### 3. Service Components

**Source:** [`oarepo_communities/services/components/`](oarepo_communities/services/components/)

Service components that integrate community functionality into record lifecycle.

#### Community Inclusion Component

Automatically adds records to their specified community on creation:

```python
from oarepo_communities.services.components.include import CommunityInclusionComponent

class MyServiceConfig(RecordServiceConfig):
    components = [
        CommunityInclusionComponent,
        # ... other components
    ]
```

#### Community Default Workflow Component

Sets the default workflow from community when creating a record:

```python
from oarepo_communities.services.components.default_workflow import (
    CommunityDefaultWorkflowComponent,
)

class MyServiceConfig(RecordServiceConfig):
    components = [
        CommunityDefaultWorkflowComponent,
        # ... other components
    ]
```

#### Community Record Access Component

Enforces access restrictions based on community visibility:

```python
from oarepo_communities.services.components.access import (
    CommunityRecordAccessComponent,
)

class MyServiceConfig(RecordServiceConfig):
    components = [
        CommunityRecordAccessComponent,  # Should be first
        # ... other components
    ]
```

### 4. Request Types

**Source:** [`oarepo_communities/requests/`](oarepo_communities/requests/)

Built-in request types for community operations.

#### Secondary Community Submission

Request to add a record to an additional community:

```python
from oarepo_communities.requests.submission_secondary import (
    SecondaryCommunitySubmissionRequestType,
)

# Submit request
request = requests_service.create(
    identity,
    data={
        "payload": {"community": "target-community-id"}
    },
    request_type="secondary_community_submission",
    topic=record,
)
```

#### Remove Secondary Community

Request to remove a record from a secondary community:

```python
from oarepo_communities.requests.remove_secondary import (
    RemoveSecondaryCommunityRequestType,
)

# Submit request
request = requests_service.create(
    identity,
    data={
        "payload": {"community": "community-to-remove"}
    },
    request_type="remove_secondary_community",
    topic=record,
)
```

#### Community Migration

Two-phase process for migrating a record's primary community:

```python
from oarepo_communities.requests.migration import (
    InitiateCommunityMigrationRequestType,
    ConfirmCommunityMigrationRequestType,
)

# Phase 1: Current community owner approves migration
request = requests_service.create(
    identity,
    data={
        "payload": {"community": "new-primary-community"}
    },
    request_type="initiate_community_migration",
    topic=record,
)

# Phase 2: Target community owner confirms (auto-created on accept)
# ConfirmCommunityMigrationRequestType is automatically triggered
```

### 5. Community Role Service

**Source:** [`oarepo_communities/services/community_role/`](oarepo_communities/services/community_role/)

Pseudo-service for managing community roles as entities in the request system:

```python
from oarepo_communities.proxies import current_oarepo_communities

# Read a community role entity
role = current_oarepo_communities.community_role_service.read(
    identity,
    id_="community-id:owner"
)

# Read multiple community roles
roles = current_oarepo_communities.community_role_service.read_many(
    identity,
    ids=["community-1:owner", "community-2:curator"]
)
```

### 6. CLI Commands

**Source:** [`oarepo_communities/cli/`](oarepo_communities/cli/)

Command-line interface for community management:

```bash
# Create a community
invenio communities create my-community "My Community Title" --public

# List all communities
invenio communities list

# Add a member to a community
invenio communities members add my-community user@example.com reader

# Add an owner to a community
invenio communities members add my-community admin@example.com owner

# Remove a member from a community
invenio communities members remove my-community user@example.com
```

### 7. Model Presets

**Source:** [`oarepo_communities/model/presets/`](oarepo_communities/model/presets/)

Integration presets for `oarepo-model` that add community support to record models:

```python
from oarepo_model.api import model
from oarepo_communities.model.presets import communities_preset

model = model(
    name="my_records",
    version="1.0.0",
    presets=[
        communities_preset,  # Adds community support
        # ... other presets
    ],
)
```

**Key preset features:**

- **ParentCommunityMetadata**: Adds community relationship to parent records
- **CommunitiesPermissionPolicy**: Replaces default permission policy with `CommunityWorkflowPermissionPolicy`
- **Service Components**: Automatically includes community-related components

### 8. Utilities and Helpers

**Source:** [`oarepo_communities/utils.py`](oarepo_communities/utils.py)

Helper functions for working with communities:

```python
from oarepo_communities.utils import (
    get_community_needs_for_identity,
    load_community_user_needs,
    community_id_from_record,
    community_to_dict,
)

# Get all community roles for a user
community_roles = get_community_needs_for_identity(identity)
# Returns: [("community-id-1", "owner"), ("community-id-2", "reader"), ...]

# Load community needs into identity
load_community_user_needs(identity)

# Extract community ID from record
community_id = community_id_from_record(record)

# Convert community to embeddable dict
community_dict = community_to_dict(community)
# Returns: {"slug": "...", "id": "...", "logo": "...", "links": {...}}
```

### 9. Notification Support

**Source:** [`oarepo_communities/notifications/`](oarepo_communities/notifications/), [`oarepo_communities/records/api.py`](oarepo_communities/records/api.py)

Community role entity for notifications and email recipients:

```python
from oarepo_communities.records.api import CommunityRoleRecord

# Create a community role record for notifications
role_record = CommunityRoleRecord(community=community, role="curator")

# Get emails of all members with this role
emails = role_record.emails
# Returns: ["curator1@example.com", "curator2@example.com", ...]
```

### 10. Entity Resolvers

**Source:** [`oarepo_communities/resolvers/communities.py`](oarepo_communities/resolvers/communities.py)

Entity resolver for community roles in the request system:

```python
# Automatically registered, allows referencing community roles in requests
{
    "receiver": {"community_role": "community-id:owner"}
}
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/oarepo/oarepo-communities.git
cd oarepo-communities

./run.sh venv
```

### Running Tests

```bash
./run.sh test
```

## Entry Points

The package registers several Invenio entry points:

```python
[project.entry-points."invenio_base.api_apps"]
oarepo_communities = "oarepo_communities.ext:OARepoCommunities"

[project.entry-points."invenio_base.apps"]
oarepo_communities = "oarepo_communities.ext:OARepoCommunities"

[project.entry-points."invenio_requests.entity_resolvers"]
community_role = "oarepo_communities.resolvers.communities:CommunityRoleResolver"

[project.entry-points."invenio_requests.types"]
confirm-community-migration = "oarepo_communities.requests.migration:ConfirmCommunityMigrationRequestType"
initiate-community-migration = "oarepo_communities.requests.migration:InitiateCommunityMigrationRequestType"
remove-secondary-community = "oarepo_communities.requests.remove_secondary:RemoveSecondaryCommunityRequestType"
secondary-community-submission = "oarepo_communities.requests.submission_secondary:SecondaryCommunitySubmissionRequestType"

[project.entry-points."oarepo_workflows.default_workflow_getters"]
community-default-workflow = "oarepo_communities.workflow:community_default_workflow"

[project.entry-points."invenio_config.module"]
oarepo_communities = "oarepo_communities.initial_config"
```

## Configuration

### Key Configuration Options

```python
# Default workflow for communities without explicit workflow
OAREPO_COMMUNITIES_DEFAULT_WORKFLOW = "default"

# Default receiver for workflow-based requests
OAREPO_REQUESTS_DEFAULT_RECEIVER = "oarepo_requests.receiver.default_workflow_receiver_function"

# Allowed request receivers
REQUESTS_ALLOWED_RECEIVERS = ["community_role"]

# Display user communities in UI
DISPLAY_USER_COMMUNITIES = True

# Display new communities section in UI
DISPLAY_NEW_COMMUNITIES = True

# Search across all community records
COMMUNITIES_RECORDS_SEARCH_ALL = False

# Community routes
COMMUNITIES_ROUTES = {
    "my_communities": "/me/communities",
    # ... additional routes
}
```

## License

Copyright (c) 2020-2025 CESNET z.s.p.o.

OARepo Communities is free software; you can redistribute it and/or modify it under the terms of the MIT License. See [LICENSE](LICENSE) file for more details.

## Links

- Documentation: <https://github.com/oarepo/oarepo-communities>
- PyPI: <https://pypi.org/project/oarepo-communities/>
- Issues: <https://github.com/oarepo/oarepo-communities/issues>
- OARepo Project: <https://github.com/oarepo>

## Acknowledgments

This project builds upon [Invenio Framework](https://inveniosoftware.org/) and [Invenio Communities](https://github.com/inveniosoftware/invenio-communities), and is developed as part of the OARepo ecosystem.
