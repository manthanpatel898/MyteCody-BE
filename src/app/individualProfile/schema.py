from dataclasses import fields
from marshmallow import Schema, fields


class IndividualUserProfileSchema(Schema):
    user_id = fields.Str(required=False)
    name = fields.Str(required=True)
    address = fields.Str(required=True)
    logo_image = fields.Str(required=False)
    website = fields.Str(required=True)
    phone_number = fields.Str(required=True)  # Store as string
    email = fields.Email(required=True)
    company_name = fields.Str(required=True)
