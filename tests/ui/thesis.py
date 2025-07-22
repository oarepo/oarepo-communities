from oarepo_ui.resources import (
    BabelComponent,
    PermissionsComponent,
    RecordsUIResourceConfig,
)
from oarepo_ui.resources.components.bleach import AllowedHtmlTagsComponent
from oarepo_ui.resources.components.custom_fields import CustomFieldsComponent
import marshmallow as ma
from flask_resources import MarshmallowSerializer, JSONSerializer, BaseListSchema


class ModelSchema(ma.Schema):
    title = ma.fields.String()

    class Meta:
        unknown = ma.INCLUDE


class ModelUISerializer(MarshmallowSerializer):
    """UI JSON serializer."""

    def __init__(self):
        """Initialise Serializer."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=ModelSchema,
            list_schema_cls=BaseListSchema,
            schema_context={"object_key": "ui"},
        )

class ThesisUIResourceConfig(RecordsUIResourceConfig):
    api_service = "thesis"  # must be something included in oarepo, as oarepo is used in tests

    blueprint_name = "thesis"
    url_prefix = "/thesis"
    ui_serializer_class = ModelUISerializer
    templates = {
        **RecordsUIResourceConfig.templates,
    }

    components = [
        BabelComponent,
        PermissionsComponent,
        AllowedHtmlTagsComponent,
        CustomFieldsComponent,
    ]