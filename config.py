import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    MONGO_URI = os.environ.get("MONGO_URI")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-secret")
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_CSRF_PROTECT = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Safety check
    if not MONGO_URI:
        raise ValueError("MONGO_URI environment variable is not set!")