from oarepo_communities.records.models import CommunityWorkflowModel


def test_change_workflow(
    logged_client,
    community_owner,
    community_with_default_workflow,
    search_clear,
):
    owner_client = logged_client(community_owner)
    owner_client.post(
        f"/communities/{community_with_default_workflow.id}/workflow/lalala"
    )

    def check_community_workflow_change(community_id, workflow):
        record = CommunityWorkflowModel.query.filter(
            CommunityWorkflowModel.community_id == community_id
        ).one()
        assert record.workflow == workflow

    check_community_workflow_change(str(community_with_default_workflow.id), "lalala")
