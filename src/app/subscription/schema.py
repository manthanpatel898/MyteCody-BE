from marshmallow import Schema, fields, post_load
class StripeProductSchema(Schema):
    id = fields.Str(required=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    price = fields.Float(required=True)
    priceId = fields.Str(required=True)

class CeratePaymentSchema(Schema):
    priceId = fields.Str(required=True)

class OrderSchema(Schema):
    _id = fields.Str(dump_only=True)
    payment_status = fields.Str(required=True)
    user_id = fields.Str(required=True)
    plan = fields.Str(required=True)
    amount = fields.Float(required=True)
    charges = fields.Float(required=True)
    # discount = fields.Float(required=True)
    payment_intent = fields.Str(required=True)
    payment_info = fields.Dict(required=True)
    purchased_date = fields.DateTime(required=True)

class SubscriptionSchema(Schema):
    _id = fields.Str(dump_only=True)
    order_id = fields.Str(required=True)
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)
    user_id = fields.Str(required=True)

class Wallet(Schema):
    amount = fields.Number(required=False)
