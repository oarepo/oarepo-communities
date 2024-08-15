from invenio_records_resources.services.records.components.base import ServiceComponent

from oarepo_communities.proxies import current_oarepo_communities


class CommunityDefaultWorkflowComponent(ServiceComponent):

    def create(self, identity, data=None, **kwargs):
        try:
            data["parent"]["workflow"]
        except KeyError:
            workflow_id = current_oarepo_communities.get_community_default_workflow(
                data=data
            )
            data.setdefault("parent", {})["workflow"] = workflow_id
