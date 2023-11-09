from collections import defaultdict

from invenio_records_resources.services.records.components import ServiceComponent

from ..proxies import current_communities_permissions


class AllowedActionsComponent(ServiceComponent):
    def _get_available_actions(self, identity, record, dict_to_save_result, **kwargs):
        record_communities = set(record["parent"]["communities"]["ids"])

        usercommunities2roles = defaultdict(list)
        communities_permissions = {}
        for need in identity.provides:
            if need.method == "community" and need.value in record_communities:
                usercommunities2roles[need.value].append(need.role)
                communities_permissions[need.value] = current_communities_permissions(
                    need.value
                )

        allowed_actions_for_record_and_user = set()
        for user_community, user_roles_community in usercommunities2roles.items():
            if user_community in record_communities:
                for user_role_community in user_roles_community:
                    permissions = communities_permissions[user_community][
                        user_role_community
                    ]
                    allowed_actions_for_record_and_user |= {
                        permission
                        for permission, allowed in permissions.items()
                        if allowed
                    }

        dict_to_save_result = kwargs[dict_to_save_result]
        dict_to_save_result["allowed_actions"] = allowed_actions_for_record_and_user

    def before_ui_detail(self, identity, data=None, record=None, errors=None, **kwargs):
        self._get_available_actions(identity, record, "extra_context", **kwargs)
