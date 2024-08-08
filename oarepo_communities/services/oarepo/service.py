from invenio_communities.communities.records.api import Community
from invenio_records_resources.services.base.service import Service
from invenio_records_resources.services.uow import RecordCommitOp, unit_of_work

from oarepo_communities.services.oarepo.uow import CommunityWorkflowCommitOp


class OARepoCommunityService(Service):
    # commentary - ref resource
    @unit_of_work()
    def set_community_workflow(
        self, identity, community_id, workflow, uow=None, **kwargs
    ):
        # todo temporarily turned off for nrdocs testing reasons
        # allowing to change workflow might effectively prevent from ever changing back
        # self.require_permission(identity, action_name="set_workflow", community_id=community_id, workflow=workflow, **kwargs)
        uow.register(CommunityWorkflowCommitOp(community_id, workflow))
        community = Community.get_record(community_id)
        community.custom_fields["workflow"] = workflow
        # uow.register(RecordCommitOp(community, indexer=current_communities.service.indexer))
        uow.register(RecordCommitOp(community))
        return {"community_id": community_id, "workflow": workflow}
