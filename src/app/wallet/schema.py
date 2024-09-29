from marshmallow import Schema, fields, post_load
class RechargeSchema(Schema):
    tokens = fields.Number(required=False)
