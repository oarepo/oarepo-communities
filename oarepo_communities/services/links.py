from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Dict

from invenio_communities.communities.records.api import Community
from invenio_records_resources.services.base.links import Link, preprocess_vars
from uritemplate import URITemplate

if TYPE_CHECKING:
    from invenio_drafts_resources.records import Record


class CommunitiesLinks(Link):
    """Utility class for keeping track of and resolve links."""

    def __init__(
        self, uritemplate_strs: Dict, when: callable = None, vars: callable = None
    ) -> None:
        """Constructor."""
        self._uritemplates = {k: URITemplate(v) for k, v in uritemplate_strs.items()}
        self._when_func = when
        self._vars_func = vars

    def expand(self, obj: Record, context: dict) -> dict:
        """Expand the URI Template."""
        ids = obj.parent.communities.ids
        links = {}
        for community_id in ids:
            vars = {}
            vars.update(deepcopy(context))
            vars["id"] = community_id
            vars["slug"] = Community.get_record(community_id).slug
            if self._vars_func:
                self._vars_func(obj, vars)
            vars = preprocess_vars(vars)
            community_links = {}
            for link_name, uritemplate in self._uritemplates.items():
                link = uritemplate.expand(**vars)
                community_links[link_name] = link
            links[community_id] = community_links
        return links
