from invenio_assets.webpack import WebpackThemeBundle

theme = WebpackThemeBundle(
    __name__,
    ".",
    default="semantic-ui",
    themes={
        "semantic-ui": dict(
            entry={"communities_landing": "./js/communities_landing/search"},
            dependencies={},
            devDependencies={},
            aliases={},
        )
    },
)
