from copy import deepcopy
from typing import Dict

from invenio_communities.communities.records.api import Community
from invenio_records_resources.services.base.links import Link, preprocess_vars
from uritemplate import URITemplate


class CommunitiesLinks(Link):
    """Utility class for keeping track of and resolve links."""

    def __init__(self, uritemplate_strs: Dict, when=None, vars=None):
        """Constructor."""
        self._uritemplates = {k: URITemplate(v) for k, v in uritemplate_strs.items()}
        self._when_func = when
        self._vars_func = vars

    def expand(self, obj, context):
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
