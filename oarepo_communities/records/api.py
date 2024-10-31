from dataclasses import dataclass

from invenio_communities.communities.records.api import Community


@dataclass
class CommunityRoleAggregate:
    community: Community
    role: str

    community_cls = Community

    @property
    def id(self):
        return f"{self.community.id}:{self.role}"

    """
    @classmethod
    def loads(cls, data, loader=None):
        role = data.pop("role")
        return cls(cls.community_cls.loads(data, loader=loader), role)


    def to_dict(self):
        return {**self.community, "role": self.role, "id": self.id}
    """
