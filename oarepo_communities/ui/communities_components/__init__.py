from oarepo_ui.resources.config import TemplatePageUIResourceConfig
from oarepo_ui.resources.resource import TemplatePageUIResource


class ComponentsResourceConfig(TemplatePageUIResourceConfig):
    url_prefix = "/communities"
    blueprint_name = "communities_components"
    template_folder = "templates"


def create_blueprint(app):
    """Register blueprint for this resource."""
    return TemplatePageUIResource(ComponentsResourceConfig()).as_blueprint()
