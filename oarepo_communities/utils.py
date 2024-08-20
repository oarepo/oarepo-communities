from flask import current_app
from invenio_communities.communities.records.api import Community
from invenio_communities.proxies import current_communities
from invenio_records_resources.proxies import current_service_registry

from oarepo_communities.proxies import current_oarepo_communities


def get_associated_service(record_service, service_type):
    # return getattr(record_service.config, service_type, None)
    return current_service_registry.get(
        f"{record_service.config.service_id}_{service_type}"
    )


def slug2id(slug):
    return str(current_communities.service.record_cls.pid.resolve(slug).id)


def get_record_services():
    services = []
    for service_id in set(current_app.config["OAREPO_PRIMARY_RECORD_SERVICE"].values()):
        services.append(current_service_registry.get(service_id))
    return services


def get_service_by_urlprefix(url_prefix):
    return current_service_registry.get(
        current_oarepo_communities.urlprefix_serviceid_mapping[url_prefix]
    )


def get_service_from_schema_type(schema_type):
    for service in get_record_services():
        if (
            hasattr(service, "record_cls")
            and hasattr(service.record_cls, "schema")
            and service.record_cls.schema.value == schema_type
        ):
            return service
    return None


def get_urlprefix_service_id_mapping():
    ret = {}
    services = get_record_services()
    for service in services:
        if hasattr(service, "config") and hasattr(service.config, "url_prefix"):
            url_prefix = service.config.url_prefix.replace(
                "/", ""
            )  # this might be problematic bc idk if there's a reason for multiword prefix - but that is a problem for using model view arg too
            ret[url_prefix] = service.config.service_id
    return ret


def community_id_from_record(record):

    if isinstance(record, Community):
        community_id = record.id
    else:
        record = record.parent if hasattr(record, "parent") else record
        try:
            community_id = record.communities.default.id
        except AttributeError:
            return None
    return community_id
