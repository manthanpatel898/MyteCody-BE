from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from multiprocessing import current_process
import os
import smtplib
from time import strptime
import uuid
import datetime
from src.app.auth.schema import ForgotPasswordSchema
from src.app.healper.validators import validate_password
from src.app.utils.messages import EMAIL_NOT_VERIFIED_MESSAGE, EMAIL_VERIFICATION_SUCCESS, INTERNAL_SERVER_ERROR_MESSAGE, INVALID_CREDENTIALS_MESSAGE, INVALID_OR_EXPIRED_TOKEN, INVALID_USER, MISSING_TOKEN_OR_PASSWORD, PASSWORD_REQUIREMENTS_MESSAGE, PASSWORD_RESET_EMAIL_SENT, PASSWORD_RESET_SUCCESS, RESET_EMAIL_TOO_RECENT, STRIPE_ERROR_MESSAGE, USER_ALREADY_EXISTS_MESSAGE, USER_CREATED_SUCCESS, USER_DOES_NOT_EXIST, USER_LOGIN_SUCCESS, USER_REGISTERED_SUCCESSFULLY_MESSAGE, VALIDATION_ERROR_MESSAGE
from src.db import db
from src.app.healper.response import make_response
from src.app.utils.constants import DEFAULT_SETTINGS, DEFAULT_TOKENS_AT_SIGNUP, TOKEN_EXPIRE_TIME
import stripe
import bcrypt
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
from marshmallow import ValidationError
from flask_jwt_extended import create_access_token
from bson import ObjectId


def register_user(data):
    try:
        email = data["email"]
        name = data["name"]
        password = data["password"]
        signup_token = str(uuid.uuid4())
        
        # Validate the password
        if not validate_password(password):
            raise ValidationError({"password": PASSWORD_REQUIREMENTS_MESSAGE})
        
        # Check if user already exists
        existing_user = db.users.find_one({"email": email})
        if existing_user:
            return make_response(
                status="error",
                message=USER_ALREADY_EXISTS_MESSAGE,
                status_code=400
            )
        
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create Stripe customer
        stripe_customer = stripe.Customer.create(
            email=email,
            name=name
        )
        
        new_user = {
            "name": name,
            "email": email,
            "password": hashed_password.decode('utf-8'),
            "is_email_verified": False,
            "signup_token": signup_token,
            "stripe_customer_id": stripe_customer['id'],
            **DEFAULT_SETTINGS,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }
        
        # Insert new user into the database
        result = db.users.insert_one(new_user)
        user_id = result.inserted_id
        
        # Create a wallet for the user
        new_wallet = {
            "user_id": user_id,
            "amountPaid": 0,
            "availableTokens": DEFAULT_TOKENS_AT_SIGNUP,
            "consumedTokens": 0,
            "totalPurchasedTokens": 0,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }
        db.wallet.insert_one(new_wallet)
        
        # Send verification email
        send_verification_email(email, name, signup_token)
        
        return make_response(
            status="success",
            message=USER_REGISTERED_SUCCESSFULLY_MESSAGE,
            data={"user_id": str(user_id)},
            status_code=201
        )
    
    except ValidationError as err:
        # Return the validation error in the required format
        return make_response(
            status="error",
            message=VALIDATION_ERROR_MESSAGE,
            data=err.messages,  # Contains detailed error messages
            status_code=400
        )
    except Exception as e:
        current_process.logger.error(f"Error in signup: {e}")
        return make_response(
            status="error",
            message=INTERNAL_SERVER_ERROR_MESSAGE,
            status_code=500
        )

def send_verification_email(email, user_name, signup_token):
    sender_email = os.environ.get("EMAIL")
    subject = "Email Verification"
    base_url = os.environ.get("BASE_URL")
    verification_link = f"{base_url}/api/auth/verify/{signup_token}"

    # Get the absolute path of the HTML file
    file_path = os.path.join(os.path.dirname(__file__), 'signup-verification.html')

    # Load the HTML template
    try:
        with open(file_path, 'r') as file:
            html_template = file.read()
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        return

    # Replace placeholders with actual values
    html_body = html_template.replace('{{ user_name }}', user_name)
    html_body = html_body.replace('{{ verification_link }}', verification_link)

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = subject

    # Attach HTML content
    msg.attach(MIMEText(html_body, "html"))

    # Convert message to string
    text = msg.as_string()

    try:
        # Log in to email server
        server = smtplib.SMTP(os.environ.get("SMTP_SERVER"), 587)
        server.starttls()
        server.login(sender_email, os.environ.get("EMAIL_PASSWORD"))
        
        # Send email
        server.sendmail(sender_email, email, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")

def signin_user(body):
    """
    Service to sign in the user and generate an access token.

    Parameters:
        body (dict): The request body containing the user's credentials (email and password).

    Returns:
        (dict): A JSON response with the access token or an error message, along with an HTTP status code.
    """
    try:
        email = body.get("email")
        password = body.get("password")

        # Check if both email and password are provided
        if not email or not password:
            return make_response(
                status="error",
                message="Email and password are required",
                status_code=400
            )

        # Find the user by email
        user = db.users.find_one({"email": email})

        # Log the user object to debug the _id issue
        print(f"Fetched user: {user}")  # This will show you the user structure

        # If the user is not found, return an error
        if not user:
            return make_response(
                status="error",
                message="Invalid email or password",
                status_code=400
            )

        # Ensure the user has an "_id" field and log the _id
        if not user.get("_id"):
            print("User object does not contain _id.")
            return make_response(
                status="error",
                message="User record is incomplete. Missing user ID.",
                status_code=500
            )

        # Log the fetched _id
        print(f"User ID: {user['_id']}")

        # Retrieve the user's password and compare
        stored_password = user.get("password")
        if not stored_password or not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            return make_response(
                status="error",
                message="Invalid email or password",
                status_code=400
            )

        # Generate access token with user's email and ID
        access_token = create_access_token(identity=user)

        # Return the access token with success message
        return make_response(
            status="success",
            message="Login successful",
            data={"access_token": access_token},
            status_code=200
        )

    except Exception as e:
        # Log the error and return an internal server error response
        print(f"Error in signin: {e}")
        return make_response(
            status="error",
            message="Internal server error occurred during sign-in",
            status_code=500
        )

def forgot_password(body):
    try:
        # data = ForgotPasswordSchema.load(body)
        email = body["email"]

        # Find user by email
        user = db.users.find_one({"email": email})
        if not user:
            return make_response(
                status="error",
                message=USER_DOES_NOT_EXIST,
                status_code=400
            )

        # Check if a reset email was sent within the last hour
        now = datetime.datetime.utcnow()
        reset_requested_at = user.get("password_reset_requested_at")
        if reset_requested_at:
            reset_requested_at = datetime.datetime.strptime(reset_requested_at, "%Y-%m-%dT%H:%M:%S.%f")
            time_since_last_request = now - reset_requested_at
            if time_since_last_request < datetime.timedelta(hours=1):
                time_remaining = datetime.timedelta(hours=1) - time_since_last_request
                minutes_remaining = int(time_remaining.total_seconds() // 60)
                return make_response(
                    status="error",
                    message=RESET_EMAIL_TOO_RECENT.format(minutes_remaining=minutes_remaining),
                    status_code=429  # Too Many Requests
                )

        # Generate signup token
        signup_token = str(uuid.uuid4())
        # Update user with new token and timestamp
        db.users.update_one(
            {"email": email},
            {"$set": {
                "signup_token": signup_token,
                "password_reset_requested_at": now.isoformat()
            }}
        )

        # Send password reset email
        send_reset_password_email(email, user['name'], signup_token)

        return make_response(
            status="success",
            message=PASSWORD_RESET_EMAIL_SENT,
            status_code=200
        )

    except ValidationError as err:
        return make_response(
            status="error",
            message=VALIDATION_ERROR_MESSAGE,
            data=err.messages,
            status_code=400
        )
    except Exception as e:
        print(f"Error in forgot password: {e}")
        return make_response(
            status="error",
            message=INTERNAL_SERVER_ERROR_MESSAGE,
            status_code=500
        )
def send_reset_password_email(email, user_name, signup_token):
    sender_email = os.environ.get("EMAIL")
    subject = "Reset Your Password"
    base_url = os.environ.get("FRONTEND_URL")
    verification_link = f"{base_url}/reset-password?token={signup_token}"

    # Get the absolute path of the HTML file
    file_path = os.path.join(os.path.dirname(__file__), 'reset-password.html')

    # Load the HTML template
    try:
        with open(file_path, 'r') as file:
            html_template = file.read()
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        return

    # Replace placeholders with actual values
    html_body = html_template.replace('{{ user_name }}', user_name)
    html_body = html_body.replace('{{ verification_link }}', verification_link)

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = email
    msg["Subject"] = subject

    # Attach HTML content
    msg.attach(MIMEText(html_body, "html"))

    # Convert message to string
    text = msg.as_string()

    try:
        # Log in to email server
        server = smtplib.SMTP(os.environ.get("SMTP_SERVER"), 587)
        server.starttls()
        server.login(sender_email, os.environ.get("EMAIL_PASSWORD"))
        
        # Send email
        server.sendmail(sender_email, email, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")
def reset_password(body):
    try:
        token = body.get("token")
        new_password = body.get("password")

        if not token or not new_password:
            return make_response(
                status="error",
                message=MISSING_TOKEN_OR_PASSWORD,
                status_code=400
            )

        user = db.users.find_one({"signup_token": token})

        if not user:
            return make_response(
                status="error",
                message=INVALID_USER,
                status_code=400
            )

        # Hash the new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # Update the user's password and clear the signup token
        db.users.update_one(
            {"signup_token": token},
            {"$set": {"password": hashed_password.decode('utf-8')}, "$unset": {"signup_token": ""}}
        )

        return make_response(
            status="success",
            message=PASSWORD_RESET_SUCCESS,
            status_code=200
        )

    except Exception as e:
        print(f"Error in reset password: {e}")
        return make_response(
            status="error",
            message=INTERNAL_SERVER_ERROR_MESSAGE,
            status_code=500
        )

def verify_user_email(signup_token):
    try:
        # Find the user with the matching signup_token
        user = db.users.find_one({"signup_token": signup_token})
        
        if not user:
            # If no user is found with the provided signup_token, return an error
            return make_response(
                status="error",
                message=INVALID_OR_EXPIRED_TOKEN,
                status_code=400
            )
        
        # If a user is found, update the user's record to set is_email_verified to True and remove the signup_token
        db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"is_email_verified": True},
                "$unset": {"signup_token": ""}
            }
        )
        
        # Redirect the user to the sign-in page
        base_url = os.environ.get("FRONTEND_URL")
        return make_response(
            status="success",
            message=EMAIL_VERIFICATION_SUCCESS,
            data={"redirect_url": base_url + "/sign-in"},
            status_code=200
        )

    except Exception as e:
        # Handle any unexpected errors
        print(f"Error in email verification: {e}")
        return make_response(
            status="error",
            message=INTERNAL_SERVER_ERROR_MESSAGE,
            status_code=500
        )

def user_sso_login(args):
    try:
        email = args["email"]
        name = args["name"]
        oauth_type = args["oauth_type"]
        oauth_access_token = args.get("oauth_access_token", "")
        
        # Check if the provided email and oauth_type match a user in the collection
        user = db.users.find_one({"email": email})
        access_token = ""
        if user:
            # Generate access token with user's ID as the payload
            access_token = create_access_token(identity=user)
            db.users.find_one_and_update(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "email": email,
                        "oauth_type": oauth_type,
                        "oauth_access_token": oauth_access_token,
                        "name": name
                    }
                },
            )
            check = db.proposals.find_one({"user": ObjectId(user["_id"])})
            return (
                make_response(
                    status="success",
                    message=USER_LOGIN_SUCCESS,
                    data={
                        "access_token": access_token,
                        "user": {
                            "id": str(user["_id"]),
                            "email": email,
                            "name": name,
                            "oauth_type": oauth_type,
                            "oauth_access_token": oauth_access_token,
                        },
                        "has_proposals": check is not None,
                    },
                    status_code=200,
                )
            )
        else:
            # Create Stripe customer
            stripe_customer = stripe.Customer.create(
                email=email,
                name=name
            )
            
            new_user = {
                "email": email,
                "oauth_type": oauth_type,
                "oauth_access_token": oauth_access_token,
                "name": name,
                "is_email_verified": True,
                "stripe_customer_id": stripe_customer['id'],
                **DEFAULT_SETTINGS,
            }
            result = db.users.insert_one(new_user)
            new_user_id = result.inserted_id
            
            # Create a wallet for the new user
            new_wallet = {
                "user_id": new_user_id,
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow(),
                "amountPaid": 0,
                "availableTokens": DEFAULT_TOKENS_AT_SIGNUP,
                "consumedTokens": 0,
                "totalPurchasedTokens": 0
            }
            db.wallet.insert_one(new_wallet)
            
            # Generate access token for new user
            access_token = create_access_token(identity=new_user)
            return (
                make_response(
                    status="success",
                    message=USER_CREATED_SUCCESS,
                    data={
                        "access_token": access_token,
                        "user": {
                            "id": str(new_user_id),
                            "email": email,
                            "name": name,
                            "oauth_type": oauth_type,
                            "oauth_access_token": oauth_access_token,
                            "is_email_verified": True,
                            "stripe_customer_id": stripe_customer['id'],
                        },
                        "has_proposals": False,
                    },
                    status_code=200,
                )
            )
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        return make_response(
            status="error",
            message=STRIPE_ERROR_MESSAGE,
            status_code=500
        )
    except Exception as e:
        print("Error in login", e)
        return make_response(
            status="error",
            message=INTERNAL_SERVER_ERROR_MESSAGE,
            status_code=500
        )
