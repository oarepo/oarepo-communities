from invenio_assets.webpack import WebpackThemeBundle

theme = WebpackThemeBundle(
    __name__,
    ".",
    default="semantic-ui",
    themes={
        "semantic-ui": dict(
            entry={"communities_landing": "./js/oarepo_communities/search"},
            dependencies={},
            devDependencies={},
            aliases={"@js/oarepo_communities": "./js/oarepo_communities"},
        )
    },
)
