from invenio_communities.proxies import current_communities
from invenio_records_resources.proxies import current_service_registry

from oarepo_communities.proxies import current_oarepo_communities

# from oarepo_runtime.datastreams.utils import get_record_services


def get_associated_service(record_service, service_type):
    # return getattr(record_service.config, service_type, None)
    return current_service_registry.get(
        f"{record_service.config.service_id}_{service_type}"
    )


def slug2id(slug):
    return str(current_communities.service.record_cls.pid.resolve(slug).id)


from oarepo_global_search.services.records.service import GlobalSearchService
from oarepo_global_search.services.records.user_service import GlobalUserSearchService


def get_global_search_service():
    return GlobalSearchService()


def get_global_user_search_service():
    return GlobalUserSearchService()


def get_record_services():
    from oarepo_communities.proxies import current_oarepo_communities

    return current_oarepo_communities.community_records_services


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


# todo add community records services into config, use here as temp fix
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
