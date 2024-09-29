from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, current_user
from src.app.user.schema import UpdateSettingSchema
from src.app.user.services import fetch_user_settings, update_user_setting

users = Blueprint("users", __name__, url_prefix="/api/user", description="User API")

@users.route("/settings", methods=["GET"])
@jwt_required()
def get_user_settings():
    """
    API endpoint to get user settings.

    Returns:
        (dict): A JSON response containing user settings or an error message.
    """
    user = current_user
    return fetch_user_settings(user["_id"])

@users.route("/settings/update", methods=["PUT"])
@jwt_required()
@users.arguments(UpdateSettingSchema, location="json", required=True)
def update_user_settings(args):
    """
    API endpoint to update a specific user setting.

    Parameters:
        args (dict): Contains the setting key and value to be updated.

    Returns:
        (dict): A JSON response indicating the success or failure of the update.
    """
    user = current_user
    return update_user_setting(user["_id"], args)

