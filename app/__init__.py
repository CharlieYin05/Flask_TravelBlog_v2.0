from flask import Flask

from app.config import Config
from app.extensions import db, migrate, csrf, login
from app.forms import LogoutForm
from app.routes import main_bp
from app.routes.main_routes import country_to_flag


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
    app.jinja_env.filters['flag'] = country_to_flag

    @app.context_processor
    def inject_logout_form():
        return {"logout_form": LogoutForm()}

    return app
