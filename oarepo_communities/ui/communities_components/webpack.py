from invenio_assets.webpack import WebpackThemeBundle

theme = WebpackThemeBundle(
    __name__,
    ".",
    default="semantic-ui",
    themes={
        "semantic-ui": {
            "entry": {
                "communities_components": "./js/communities_components/custom-components.js"
            },
            "dependencies": {},
            "devDependencies": {},
            "aliases": {
                "@js/communities_components": "./js/communities_components/components"
            },
        }
    },
)
