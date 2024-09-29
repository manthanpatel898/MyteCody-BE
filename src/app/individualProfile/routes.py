from flask_jwt_extended import current_user, jwt_required
from flask_smorest import Blueprint
from src.app.individualProfile.schema import IndividualUserProfileSchema
from src.app.individualProfile.services import create_user_profile_service, delete_user_profile_service, get_user_profile_service, update_user_profile_service


individual_profile_bp = Blueprint("individual_profiles", __name__, url_prefix="/api/individual", description="Individual User Profile API")


@individual_profile_bp.post("/user/profile")
@individual_profile_bp.arguments(IndividualUserProfileSchema, location="json")
@jwt_required()
def create_profile(body):
    """
    Endpoint to create a new user profile.
    
    Parameters:
        body (dict): Request body containing profile details.
    
    Returns:
        (dict): A JSON response with status, message, and data.
    """
    user = current_user
    return create_user_profile_service(body, user["_id"])

@individual_profile_bp.get("/user/profile")
@jwt_required()
def fetch_profile():
    """
    Endpoint to get the user's profile.
    
    Returns:
        (dict): A JSON response with profile details or error message.
    """
    user = current_user
    return get_user_profile_service(user["_id"])

@individual_profile_bp.put("/user/profile")
@individual_profile_bp.arguments(IndividualUserProfileSchema, location="json")
@jwt_required()
def modify_profile(body):
    """
    Endpoint to update the user profile.
    
    Parameters:
        body (dict): Request body containing updated profile details.
    
    Returns:
        (dict): A JSON response with status and message.
    """
    user = current_user
    return update_user_profile_service(user["_id"], body)

@individual_profile_bp.delete("/user/profile/<string:user_id>")
@jwt_required()
def remove_profile(user_id):
    """
    Endpoint to delete a user profile.
    
    Parameters:
        user_id (str): ID of the user whose profile needs to be deleted.
    
    Returns:
        (dict): A JSON response with status and message.
    """
    return delete_user_profile_service(user_id)
