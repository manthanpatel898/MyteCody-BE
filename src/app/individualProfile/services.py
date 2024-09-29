from bson import ObjectId
from src.app.healper.response import make_response
from src.app.utils.messages import DB_ERROR, DUPLICATE_KEY_ERROR, NO_PROFILE_CHANGES, PROFILE_ALREADY_EXISTS, PROFILE_CREATED_SUCCESS, PROFILE_DELETED_SUCCESS, PROFILE_FETCHED_SUCCESS, PROFILE_NOT_FOUND, PROFILE_UPDATED_SUCCESS, UNEXPECTED_ERROR
from src.app.utils.userTypeEnum import INDIVIDUAL_USER_TYPE
from src.db import db

def create_user_profile_service(body, user_id):
    """
    Service to create a new user profile.

    Parameters:
        body (dict): Profile data.
        user_id (str): ID of the current user.

    Returns:
        (dict): A standard response JSON using make_response.
    """
    try:
        profile_exists = db.individual_profiles.find_one({"user_id": user_id})

        if profile_exists:
            return make_response(
                status="error",
                message=PROFILE_ALREADY_EXISTS,
                data=None,
                status_code=400
            )
        
        body["user_id"] = user_id
        db.individual_profiles.insert_one(body)

        db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"userType": INDIVIDUAL_USER_TYPE}})

        return make_response(
            status="success",
            message=PROFILE_CREATED_SUCCESS,
            data={"user_id": str(user_id)},
            status_code=200
        )

    except DUPLICATE_KEY_ERROR:
        return make_response(
            status="error",
            message=DUPLICATE_KEY_ERROR,
            data=None,
            status_code=409
        )
    except Exception as e:
        return make_response(
            status="error",
            message=UNEXPECTED_ERROR,
            data=None,
            status_code=500
        )

def get_user_profile_service(user_id):
    """
    Service to get a user profile.

    Parameters:
        user_id (str): ID of the user.

    Returns:
        (dict): A standard response JSON using make_response.
    """
    try:
        profile = db.individual_profiles.find_one({"user_id": ObjectId(user_id)})

        if not profile:
            return make_response(
                status="error",
                message=PROFILE_NOT_FOUND,
                data=None,
                status_code=404
            )

        profile["_id"] = str(profile["_id"])
        profile["user_id"] = str(profile["user_id"])

        return make_response(
            status="success",
            message=PROFILE_FETCHED_SUCCESS,
            data=profile,
            status_code=200
        )
    except Exception as e:
        return make_response(
            status="error",
            message=UNEXPECTED_ERROR,
            data=None,
            status_code=500
        )

def update_user_profile_service(user_id, body):
    """
    Service to update a user profile.

    Parameters:
        user_id (str): ID of the user.
        body (dict): Updated profile data.

    Returns:
        (dict): A standard response JSON using make_response.
    """
    try:
        profile_exists = db.individual_profiles.find_one({"user_id": ObjectId(user_id)})

        if not profile_exists:
            return make_response(
                status="error",
                message=PROFILE_NOT_FOUND,
                data=None,
                status_code=404
            )

        result = db.individual_profiles.update_one({"user_id": ObjectId(user_id)}, {"$set": body})

        if result.modified_count > 0:
            return make_response(
                status="success",
                message=PROFILE_UPDATED_SUCCESS,
                data=None,
                status_code=200
            )
        else:
            return make_response(
                status="info",
                message=NO_PROFILE_CHANGES,
                data=None,
                status_code=200
            )

    except Exception as e:
        return make_response(
            status="error",
            message=UNEXPECTED_ERROR,
            data=None,
            status_code=500
        )

def delete_user_profile_service(user_id):
    """
    Service to delete a user profile.

    Parameters:
        user_id (str): ID of the user.

    Returns:
        (dict): A standard response JSON using make_response.
    """
    try:
        result = db.individual_profiles.delete_one({"user_id": ObjectId(user_id)})

        if result.deleted_count > 0:
            return make_response(
                status="success",
                message=PROFILE_DELETED_SUCCESS,
                data=None,
                status_code=200
            )
        else:
            return make_response(
                status="error",
                message=PROFILE_NOT_FOUND,
                data=None,
                status_code=404
            )

    except Exception as e:
        return make_response(
            status="error",
            message=UNEXPECTED_ERROR,
            data=None,
            status_code=500
        )
