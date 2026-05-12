from flask import Flask, session

from app.config import Config
from app.extensions import db, migrate, csrf, login
from app.routes import main_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login.init_app(app)
    login.login_view = "main.signin"

    from app import models

    app.register_blueprint(main_bp)

    @app.context_processor
    def inject_current_user():
        from app.models import User
        username = session.get("user")
        if username:
            user = User.query.filter_by(username=username).first()
        else:
            user = None
        return {"current_user": user}

    return app
