from .submission import CommunitySubmission, AcceptAction


class MigrateAcceptAction(AcceptAction):
    """Accept action."""

    def execute(self, identity, uow):
        super().execute(identity, uow)

class MigrateCommunity(CommunitySubmission):
    """Review request for submitting a record to a community."""

    type_id = "migrate-community"
    name = _("Migrate Community")

    creator_can_be_none = False
    topic_can_be_none = False
    allowed_creator_ref_types = ["user"]
    allowed_receiver_ref_types = ["community"]
    allowed_topic_ref_types = ["record"]
    needs_context = {
        "community_roles": ["owner", "manager", "curator"],
    }

    available_actions = {
        "create": actions.CreateAction,
        "submit": SubmitAction,
        "delete": actions.DeleteAction,
        "accept": AcceptAction,
        "decline": DeclineAction,
        "cancel": CancelAction,
        "expire": ExpireAction,
    }