import os
from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
from src.app.healper.response import handle_exception, handle_marshmallow_validation

from src.db import db
from src.config import Config
from src.app.auth.routes import auth
from src.app.proposal.routes import proposals
from src.app.user.routes import users
from src.app.individualProfile.routes import individual_profile_bp
from src.app.wallet.routes import wallet_bp
from src.app.subscription.routes import subscription_bp
from marshmallow import ValidationError

load_dotenv()

def create_app():
    """Create the Flask application instance"""
    app = Flask(__name__)
    jwt = JWTManager(app)

    # Explicitly configure CORS for your React app (localhost or production)
    CORS(app, resources={r"/*": {"origins": "*"}},
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"])



    app.config.from_object(Config)

    api = Api(app)

    api.register_blueprint(auth)
    api.register_blueprint(proposals)
    api.register_blueprint(users)
    api.register_blueprint(individual_profile_bp)
    api.register_blueprint(wallet_bp)
    api.register_blueprint(subscription_bp)
    
    # Register error handlers
    app.register_error_handler(ValidationError, handle_marshmallow_validation)
    app.register_error_handler(Exception, handle_exception)

    @jwt.user_identity_loader
    def user_identity_lookup(user_data):
        user_data["_id"] = str(user_data["_id"])
        data = {key: user_data[key] for key in ["_id", "email"]}
        return data

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return db.users.find_one({"email": identity["email"]})

    # @app.errorhandler(Exception)
    # def handle_exception(e):
    #     """Return JSON instead of HTML for all exceptions."""
    #     # start with the correct headers and status code
    #     response = jsonify(
    #         {
    #             "error": str(e),
    #         }
    #     )
    #     response.status_code = 500
    #     return response

    return app
