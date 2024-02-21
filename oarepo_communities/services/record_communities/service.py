from invenio_communities.proxies import current_communities
from invenio_drafts_resources.services import RecordService

# from invenio_i18n import lazy_gettext as _
# from invenio_notifications.services.uow import NotificationOp
from invenio_pidstore.errors import PIDUnregistered
from invenio_records_resources.services import RecordIndexerMixin, ServiceSchemaWrapper
from invenio_records_resources.services.uow import (
    RecordCommitOp,
    RecordIndexOp,
    unit_of_work,
)
from invenio_search.engine import dsl

from oarepo_communities.services.errors import RecordCommunityMissing


class RecordCommunitiesService(RecordService, RecordIndexerMixin):
    """Record communities service.

    The communities service is in charge of managing communities of a given record.
    """

    def __init__(self, config, record_service=None):
        super().__init__(config)
        self.record_service = record_service

    @property
    def schema(self):
        """Returns the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.schema)

    @property
    def record_cls(self):
        """Factory for creating a record class."""
        return self.config.record_cls

    def _resolve_record(self, id_):
        try:
            return self.record_cls.pid.resolve(id_)
        except PIDUnregistered:
            return self.draft_cls.pid.resolve(id_, registered_only=False)

    # todo supplied by submission secondary and migrate request
    """
    @unit_of_work()
    def add(self, identity, id_, data, uow=None):
        
    
        record = self._resolve_record(id_)
        valid_data, errors = self.schema.load(
            data,
            context={
                "identity": identity,
                "max_number": self.config.max_number_of_additions,
            },
            raise_errors=True,
        )
        communities = valid_data["communities"]
        self.require_permission(
            identity, "user_add_communities_to_records", record=record
        )

        processed = []
        for community in communities:
            community_id = community["id"]
            comment = community.get("comment", None)
            require_review = community.get("require_review", False)

            result = {
                "community_id": community_id,
            }
            try:
                self._include(
                    identity, community_id, comment, require_review, record, uow
                )
                # result["request_id"] = str(request_item.data["id"])
                # result["request"] = request_item.to_dict()
                processed.append(result)
                # uow.register(
                #    NotificationOp(
                #        CommunityInclusionSubmittedNotificationBuilder.build(
                #            request_item._request
                #        )
                #    )
                # )
            except (NoResultFound, PIDDoesNotExistError):
                # todo ask about the underscore (translation?)
                result["message"] = "Community not found."
                errors.append(result)
            except (
                CommunityAlreadyExists,
                # OpenRequestAlreadyExists,
                # InvalidAccessRestrictions,
                PermissionDeniedError,
            ) as ex:
                result["message"] = ex.description
                errors.append(result)

        uow.register(IndexRefreshOp(indexer=self.indexer))

        return processed, errors
        
    
    def _include(self, identity, community_id, comment, require_review, record, uow):
        # check if the community exists
        # todo is it necesarry to use the service here
        community = current_communities.service.record_cls.pid.resolve(community_id)
        com_id = str(community.id)

        already_included = com_id in record.parent.communities
        if already_included:
            raise CommunityAlreadyExists()

        # check if there is already an open request, to avoid duplications
        # existing_request_id = self._exists(identity, com_id, record)
        # if existing_request_id:
        #    raise OpenRequestAlreadyExists(existing_request_id)

        # type_ = current_request_type_registry.lookup(CommunityInclusion.type_id)
        # receiver = ResolverRegistry.resolve_entity_proxy(
        #    {"community": com_id}
        # ).resolve()

        # request_item = current_requests_service.create(
        #    identity,
        #    {},
        #    type_,
        #    receiver,
        #    topic=record,
        #    uow=uow,
        # )

        # create review request
        # request_item = current_rdm_records.community_inclusion_service.submit(
        #    identity, record, community, request_item._request, comment, uow
        # )
        # include directly when allowed
        # if not require_review:
        #    request_item = current_rdm_records.community_inclusion_service.include(
        #        identity, community, request_item._request, uow
        #    )

        # result = current_rdm_records.community_inclusion_service.include(
        #        identity, community, request_item._request, uow
        # )

        # return result
        self.require_permission(
            identity, "community_allows_adding_records", community=community
        )
        self.include(
            record, community, uow, record_service=self.record_service
        )
        return self.result_item()
    """

    @unit_of_work()
    def include(
        self, record, community_id, uow=None, record_service=None, default=None
    ):
        applied_record_service = record_service or self.record_service

        if default is None:
            default = not record.parent.communities
        record.parent.communities.add(community_id, default=default)
        uow.register(RecordCommitOp(record.parent))
        uow.register(RecordIndexOp(record, indexer=applied_record_service.indexer))
        return record

    @unit_of_work()
    def remove(self, record, community_id, record_service=None, uow=None):
        """Remove a community from the record."""
        applied_record_service = record_service or self.record_service
        if community_id not in record.parent.communities.ids:
            # try if it's the community slug instead
            community_id = str(
                current_communities.service.record_cls.pid.resolve(community_id).id
            )
            if community_id not in record.parent.communities.ids:
                raise RecordCommunityMissing(record.id, community_id)

        # Default community is deleted when the exact same community is removed from the record
        record.parent.communities.remove(community_id)
        uow.register(RecordCommitOp(record.parent))
        uow.register(RecordIndexOp(record, indexer=applied_record_service.indexer))

    # todo supplied by remove_secondary and migrate requests
    """
    @unit_of_work()
    def remove(self, identity, id_, data, uow=None):
        record = self._resolve_record(id_)
        valid_data, errors = self.schema.load(
            data,
            context={
                "identity": identity,
                "max_number": self.config.max_number_of_removals,
            },
            raise_errors=True,
        )
        communities = valid_data["communities"]
        processed = []
        for community in communities:
            community_id = community["id"]
            try:
                # check permission here, per community: curator cannot remove another community
                self.require_permission(
                    identity,
                    "remove_community_from_record",
                    record=record,
                    community_id=community_id,
                )
                remove(community_id, record)
                processed.append({"community": community_id})
            except (RecordCommunityMissing, PermissionDeniedError) as ex:
                errors.append(
                    {
                        "community": community_id,
                        "message": ex.description,
                    }
                )

        if processed:
            uow.register(RecordCommitOp(record.parent))
            uow.register(
                RecordIndexOp(record, indexer=self.indexer, index_refresh=True)
            )

        return processed, errors
    """

    def search(
        self,
        identity,
        id_,
        params=None,
        search_preference=None,
        expand=False,
        extra_filter=None,
        **kwargs,
    ):
        """Search for record's communities."""
        record = self._resolve_record(id_)
        self.require_permission(identity, "read", record=record)

        communities_ids = record.parent.communities.ids
        communities_filter = dsl.Q("terms", **{"id": [id_ for id_ in communities_ids]})
        if extra_filter is not None:
            communities_filter = communities_filter & extra_filter

        return current_communities.service.search(
            identity,
            params=params,
            search_preference=search_preference,
            expand=expand,
            extra_filter=communities_filter,
            **kwargs,
        )

    """
    @staticmethod
    def _get_excluded_communities_filter(record, identity, id_):
        communities_to_exclude = []
        communities_ids = record.parent.communities.ids

        for community_id in communities_ids:
            communities_to_exclude.append(dsl.Q("term", **{"id": community_id}))

        open_requests = current_requests_service.search(
            identity,
            extra_filter=dsl.query.Bool(
                "must",
                must=[
                    dsl.Q("term", **{"topic.record": id_}),
                    dsl.Q("term", **{"type": CommunityInclusion.type_id}),
                    dsl.Q("term", **{"is_open": True}),
                ],
            ),
        )

        # the assumption here is that there should be only a few open requests,
        # so requests.hits (first page one) should be enough
        for request in open_requests.hits:
            communities_to_exclude.append(
                dsl.Q("term", **{"id": request["receiver"]["community"]})
            )

        exclusion_filter = dsl.query.Bool("must_not", must_not=communities_to_exclude)

        return exclusion_filter

    def search_suggested_communities(
        self,
        identity,
        id_,
        params=None,
        search_preference=None,
        expand=False,
        by_membership=False,
        extra_filter=None,
        **kwargs
    ):

        record = self.record_cls.pid.resolve(id_)

        self.require_permission(identity, "add_community", record=record)

        communities_filter = self._get_excluded_communities_filter(
            record, identity, id_
        )

        if extra_filter is not None:
            communities_filter = communities_filter & extra_filter

        if by_membership:
            return current_communities.service.search_user_communities(
                identity,
                params=params,
                search_preference=search_preference,
                extra_filter=communities_filter,
                **kwargs
            )

        return current_communities.service.search(
            identity,
            params=params,
            search_preference=search_preference,
            expand=expand,
            extra_filter=communities_filter,
            **kwargs
        )
    """
