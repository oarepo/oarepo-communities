def community_role_mappings(identity):
    community_roles = [
        (n.value, n.role) for n in identity.provides if n.method == "community"
    ]
    return [
        {"community_role": f"{community_role[0]}:{community_role[1]}"}
        for community_role in community_roles
    ]
