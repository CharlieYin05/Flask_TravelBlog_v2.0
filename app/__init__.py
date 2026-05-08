from flask import Flask

from app.config import Config
from app.extensions import db, migrate, csrf
from app.routes import main_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    from app import models

    app.register_blueprint(main_bp)

    return app