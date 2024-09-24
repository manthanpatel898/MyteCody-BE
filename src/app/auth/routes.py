from flask_smorest import Blueprint
from src.app.auth.schema import ForgotPasswordSchema, LoginSchema, ResetPasswordSchema, SigninSchema, SignupSchema, StandardResponseSchema
from src.app.auth.services import forgot_password, register_user, reset_password, signin_user, user_sso_login, verify_user_email

auth = Blueprint("auth", __name__, url_prefix="/api/auth", description="Auth API")

@auth.route('/signup', methods=['POST'])
@auth.arguments(SignupSchema)
@auth.response(201, StandardResponseSchema)
def signup(args):
    """User Registration"""
    return register_user(args)

@auth.route('/signin', methods=['POST'])
@auth.arguments(SigninSchema)
@auth.response(201, StandardResponseSchema)
def signin(args):
    print("🚀 ~ args:", args)
    """User Registration"""
    return signin_user(args)

@auth.post("/forgot-password")
@auth.arguments(ForgotPasswordSchema, location="json")
@auth.response(201, StandardResponseSchema)
def forgotPassword(body):
    """REGISTER USER"""
    return forgot_password(body)

@auth.post("/reset-password")
@auth.arguments(ResetPasswordSchema, location="json")
@auth.response(201, StandardResponseSchema)
def resetPassword(body):
    """REGISTER USER"""
    return reset_password(body)

@auth.route("/verify/<signup_token>", methods=["GET"])
@auth.response(201, StandardResponseSchema)
def verify_email(signup_token):
    return verify_user_email(signup_token)

@auth.post("/sso/login")
@auth.arguments(LoginSchema, location="json", required=True)
@auth.response(201, StandardResponseSchema)
def login(args):
    """USER LOGIN AND TOKEN CREATION"""
    return user_sso_login(args)