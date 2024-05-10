from invenio_communities.proxies import current_communities
from invenio_records_resources.proxies import current_service_registry
from oarepo_global_search.proxies import current_global_search


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


def get_service_from_schema_type(schema_type):
    for service in current_global_search.model_services:
        if (
            hasattr(service, "record_cls")
            and hasattr(service.record_cls, "schema")
            and service.record_cls.schema.value == schema_type
        ):
            return service
    return None
