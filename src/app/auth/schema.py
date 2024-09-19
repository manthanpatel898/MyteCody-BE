from marshmallow import Schema, ValidationError, fields, validate, validates_schema
from src.app.healper.validators import validate_password


class LoginSchema(Schema):
    email = fields.Email(required=True)
    oauth_type = fields.String(
        validate=validate.OneOf(["google", "apple"]), required=True
    )
    oauth_access_token = fields.String(required=False)
    name = fields.Str(required=True)

class SignupSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1))
    email = fields.Email(required=True)
    password = fields.Str(
        required=True    )

class SigninSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=fields.Length(min=8))

class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)

class ResetPasswordSchema(Schema):
    token = fields.Str(required=True)
    password = fields.Str(required=True, validate=lambda p: len(p) >= 6, error_messages={"validator_failed": "Password must be at least 6 characters long"})

class StandardResponseSchema(Schema):
    status = fields.Str(required=True)
    message = fields.Str(required=True)
    data = fields.Dict(required=False)
