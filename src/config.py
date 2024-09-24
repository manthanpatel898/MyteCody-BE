import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PORT = 3000
    API_TITLE = os.environ.get("API_TITLE")
    API_VERSION = os.environ.get("API_VERSION")
    OPENAPI_VERSION = os.environ.get("OPENAPI_VERSION")
    OPENAPI_URL_PREFIX = os.environ.get("OPENAPI_URL_PREFIX")
    OPENAPI_SWAGGER_UI_PATH = os.environ.get("OPENAPI_SWAGGER_UI_PATH")
    OPENAPI_SWAGGER_UI_URL = os.environ.get("OPENAPI_SWAGGER_UI_URL")
    OPENAPI_REDOC_PATH = os.environ.get("OPENAPI_REDOC_PATH")
    OPENAPI_REDOC_UI_URL = os.environ.get("OPENAPI_REDOC_UI_URL")
    MONGO_URI = os.environ.get("MONGO_URI")
    DB_NAME = os.environ.get("DB_NAME")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    print("🚀 ~ JWT_SECRET_KEY:", JWT_SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 86400
    GOOGLE_AUT_CLIENT_ID = os.environ.get("GOOGLE_AUT_CLIENT_ID")
    GOOGLE_AUTH_CLIENT_SECRET = os.environ.get("GOOGLE_AUTH_CLIENT_SECRET")
    GOOGLE_AUTH_CALLBACK_URL = os.environ.get("GOOGLE_AUTH_CALLBACK_URL")
