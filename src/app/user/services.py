from src.db import db
from src.app.healper.response import make_response
from bson import ObjectId


def fetch_user_settings(user_id):
    """
    Service to fetch user settings from the database based on user ID.

    Parameters:
        user_id (str): The ID of the user whose settings are to be fetched.

    Returns:
        (dict): A JSON response with user settings or an error message.
    """
    try:
        # Fetch user data from the database
        user_data = db.users.find_one({"_id": ObjectId(user_id)}, {"settings": 1})

        if not user_data:
            return make_response(
                status="error",
                message="User not found.",
                data=None,
                status_code=404
            )
        
        # Return user settings
        return make_response(
            status="success",
            message="User settings fetched successfully.",
            data=user_data["settings"],
            status_code=200
        )

    except Exception as e:
        print(f"Error in fetching user settings: {e}")
        return make_response(
            status="error",
            message="Internal Server Error",
            data=None,
            status_code=500
        )

def update_user_setting(user_id, data):
    """
    Service to update a specific setting in the user's settings.

    Parameters:
        user_id (str): The ID of the user whose settings are to be updated.
        data (dict): Contains the setting key and value to update.

    Returns:
        (dict): A JSON response indicating the success or failure of the update.
    """
    try:
        setting_key = data.get("setting_key")
        setting_value = data.get("setting_value")

        # Ensure both key and value are provided
        if not setting_key or setting_value is None:
            return make_response(
                status="error",
                message="Invalid request. 'setting_key' and 'setting_value' are required.",
                data=None,
                status_code=400
            )

        # Create the update query dynamically
        update_query = {f"settings.{setting_key}": setting_value}

        # Update the user's settings in the database
        result = db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_query})

        if result.matched_count == 0:
            return make_response(
                status="error",
                message="User not found or no changes made.",
                data=None,
                status_code=404
            )

        return make_response(
            status="success",
            message=f"User setting '{setting_key}' updated successfully.",
            data=None,
            status_code=200
        )

    except Exception as e:
        print(f"Error in updating user setting: {e}")
        return make_response(
            status="error",
            message="Internal Server Error",
            data=None,
            status_code=500
        )
