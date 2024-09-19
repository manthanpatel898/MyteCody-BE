from flask import jsonify, current_app
from src.app.utils.messages import INTERNAL_SERVER_ERROR_MESSAGE, VALIDATION_ERROR_MESSAGE

def make_response(status, message, data=None, status_code=200):
    response = {
        "status": status,
        "message": message
    }
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code

def send_verification_email(email, name, signup_token):
    # Implement email sending logic here
    pass

def handle_marshmallow_validation(err):
    return make_response(
        status="error",
        message=VALIDATION_ERROR_MESSAGE,
        data=err.messages,
        status_code=400
    )

def handle_exception(err):
    current_app.logger.error(f"Unhandled exception: {err}")
    return make_response(
        status="error",
        message=INTERNAL_SERVER_ERROR_MESSAGE,
        status_code=500
    )
