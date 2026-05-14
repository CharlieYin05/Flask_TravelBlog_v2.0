import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'app.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")


class ProductionConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY")