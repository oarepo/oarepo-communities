from marshmallow import Schema, fields


class CommunitiesParentSchema(Schema):

    ids = fields.List(fields.String())
    default = fields.String()