from invenio_communities.communities.records.api import Community
from invenio_communities.proxies import current_communities
from invenio_records_resources.proxies import current_service_registry
from oarepo_requests.utils import get_from_requests_workflow, workflow_from_record
from oarepo_workflows.permissions.generators import reference_receiver_from_generators

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
        # todo this could be problem for invenio too, as they have the same
        # community_id = record.id and what is record depends on context - see the need for unified meaning of
        # permission kwargs
        # we shouldn't have to write complicated checks like this
        # this is hack that falls apart with different communityrecord class
    if isinstance(record, Community):
        community_id = record.id
    else:
        record = record.parent if hasattr(record, "parent") else record
        try:
            community_id = record.communities.default.id
        except AttributeError:
            return None
    return community_id

def workflow_receiver_function(record=None, request_type=None, **kwargs):
    workflow_id = workflow_from_record(record)
    try:
        recipients_generators = get_from_requests_workflow(workflow_id, request_type.type_id, "recipients")
    except KeyError:
        return None
    return reference_receiver_from_generators(recipients_generators, record=record, request_type=request_type, **kwargs)

def parse_community_ref_value(value):
    return value.split()


def community_in_payload_entity_ref(**kwargs):
    data = kwargs["data"]
    target_community = data["payload"]["community"]
    return {"community": target_community}

def community_in_topic_entity_ref(**kwargs):
    topic = kwargs["topic"]
    return {"community": str(topic.parent.communities.default.id)}


from invenio_records.dictutils import parse_lookup_key
def mixed_dict_lookup(source, lookup_key, parent=False):
    """Make a lookup into a dict based on a dot notation.

    Examples of the supported dot notation:

    - ``'a'`` - Equivalent to ``source['a']``
    - ``'a.b'`` - Equivalent to ``source['a']['b']``
    - ``'a.b.0'`` - Equivalent to ``source['a']['b'][0]`` (for lists)

    List notation is also supported:

    - `['a']``
    - ``['a','b']``
    - ``['a','b', 0]``

    :param source: The dictionary object to perform the lookup in.
    :param parent: If parent argument is True, returns the parent node of
                   matched object.
    :param lookup_key: A string using dot notation, or a list of keys.
    """
    # Copied from dictdiffer (CERN contributed part) and slightly modified.
    keys = parse_lookup_key(lookup_key)

    if parent:
        keys = keys[:-1]

    # Lookup the key
    value = source
    for key in keys:
        try:
            if isinstance(value, list):
                key = int(key)
            if hasattr(value, key):
                value = getattr(value, key)
            else:
                value = value[key]
        except (TypeError, IndexError, ValueError, KeyError) as exc:
            raise KeyError(lookup_key) from exc
    return value