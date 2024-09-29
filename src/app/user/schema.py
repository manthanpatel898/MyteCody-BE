from dataclasses import fields
from marshmallow import Schema, fields


class UpdateSettingSchema(Schema):
    setting_key = fields.Str(required=True, description="The key of the setting to update (e.g., 'level_of_complexities.Very_Simple')")
    setting_value = fields.Float(required=True, description="The new value for the setting")
