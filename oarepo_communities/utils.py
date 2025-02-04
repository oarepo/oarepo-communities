from __future__ import annotations

from typing import TYPE_CHECKING

from flask import current_app, session
from invenio_communities.communities.records.api import Community
from invenio_communities.proxies import current_communities, current_identities_cache
from invenio_communities.utils import identity_cache_key
from invenio_records_resources.proxies import current_service_registry

from oarepo_communities.proxies import current_oarepo_communities
from oarepo_communities.services.permissions.generators import UserInCommunityNeed

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records_resources.records import Record
    from invenio_records_resources.services.records.service import RecordService


def get_community_needs_for_identity(
    identity: Identity,
) -> list[tuple[str, str]] | None:
    # see invenio_communities.utils.load_community_needs
    if identity.id is None:
        # no user is logged in
        return

    cache_key = identity_cache_key(identity)
    community_roles = current_identities_cache.get(cache_key)
    if community_roles is None:
        # aka Member.get_memberships(identity)
        roles_ids = session.get("unmanaged_roles_ids", [])

        member_cls = current_communities.service.members.config.record_cls
        managed_community_roles = member_cls.get_memberships(identity)
        unmanaged_community_roles = member_cls.get_memberships_from_group_ids(
            identity, roles_ids
        )
        community_roles = managed_community_roles + unmanaged_community_roles

        current_identities_cache.set(
            cache_key,
            community_roles,
        )
    return community_roles


def load_community_user_needs(identity: Identity) -> None:
    # todo assuming there's one user and identity_id = user_id
    community_roles = get_community_needs_for_identity(identity)
    if not community_roles:
        return
    communities = {community_role[0] for community_role in community_roles}
    needs = {UserInCommunityNeed(identity.id, community) for community in communities}
    identity.provides |= needs


def get_associated_service(
    record_service: RecordService, service_type: str
) -> RecordService:
    # return getattr(record_service.config, service_type, None)
    return current_service_registry.get(
        f"{record_service.config.service_id}_{service_type}"
    )


def slug2id(slug: str) -> str:
    return str(current_communities.service.record_cls.pid.resolve(slug).id)


def get_record_services() -> list[RecordService]:
    services = []
    for service_id in set(current_app.config["OAREPO_PRIMARY_RECORD_SERVICE"].values()):
        services.append(current_service_registry.get(service_id))
    return services


def get_service_by_urlprefix(url_prefix: str) -> RecordService:
    return current_service_registry.get(
        current_oarepo_communities.urlprefix_serviceid_mapping[url_prefix]
    )


def get_service_from_schema_type(schema_type: str) -> RecordService:
    for service in get_record_services():
        if (
            hasattr(service, "record_cls")
            and hasattr(service.record_cls, "schema")
            and service.record_cls.schema.value == schema_type
        ):
            return service


def get_urlprefix_service_id_mapping() -> dict[str, str]:
    ret = {}
    services = get_record_services()
    for service in services:
        if hasattr(service, "config") and hasattr(service.config, "url_prefix"):
            url_prefix = service.config.url_prefix.replace(
                "/", ""
            )  # this might be problematic bc idk if there's a reason for multiword prefix - but that is a problem for using model view arg too
            ret[url_prefix] = service.config.service_id
    return ret


def community_id_from_record(record: Record) -> str | None:
    if isinstance(record, Community):
        community_id = record.id
    else:
        record = record.parent if hasattr(record, "parent") else record
        try:
            community_id = record.communities.default.id
        except AttributeError:
            return None
    return community_id


def community_to_dict(community):
    return {
        "slug": str(community.slug),
        "id": str(community.id),
        "logo": f"/api/communities/{community.id}/logo",
        "links": {
            "self_html": f"/communities/{community.id}/records",
        },
        **(community.metadata or {}),
    }
