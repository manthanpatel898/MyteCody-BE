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
from marshmallow import ValidationError

load_dotenv()

def create_app():
    """Create the Flask application instance"""
    app = Flask(__name__)
    jwt = JWTManager(app)
    CORS(app)

    app.config.from_object(Config)

    api = Api(app)

    api.register_blueprint(auth)

    # Register error handlers
    app.register_error_handler(ValidationError, handle_marshmallow_validation)
    app.register_error_handler(Exception, handle_exception)


    return app
