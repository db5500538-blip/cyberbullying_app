import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/ethoria")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_CSRF_PROTECT = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024