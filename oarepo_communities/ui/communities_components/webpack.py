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
            "dependencies": {
                "react-searchkit": "^2.0.0",
            },
            "devDependencies": {},
            "aliases": {},
        }
    },
)
