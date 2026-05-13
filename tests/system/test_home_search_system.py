import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from werkzeug.serving import make_server

from app.extensions import csrf, db, login
from app.forms import LogoutForm
from app.models import User
from app.routes import main_bp

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class LiveServerThread(threading.Thread):
    def __init__(self, app, host="127.0.0.1", port=0):
        super().__init__(daemon=True)

        self.server = make_server(host, port, app)
        self.host = host
        self.port = self.server.server_port

        self.context = app.app_context()
        self.context.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.context.pop()

class HomeSearchSystemTests(unittest.TestCase):

    def create_webdriver(self):
        browser = os.environ.get(
            "SELENIUM_BROWSER",
            ""
        ).lower().strip()

        def make_chrome():
            options = ChromeOptions()

            options.add_argument("--headless=new")
            options.add_argument("--window-size=1400,1000")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            options.add_argument(
                f"--user-data-dir="
                f"{os.path.join(self.browser_profile_dir, 'chrome')}"
            )

            return webdriver.Chrome(options=options)

        def make_edge():
            options = EdgeOptions()

            options.add_argument("--headless=new")
            options.add_argument("--window-size=1400,1000")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            options.add_argument(
                f"--user-data-dir="
                f"{os.path.join(self.browser_profile_dir, 'edge')}"
            )

            return webdriver.Edge(options=options)

        def make_firefox():
            options = FirefoxOptions()
            options.add_argument("--headless")

            return webdriver.Firefox(options=options)

        browsers = {
            "chrome": make_chrome,
            "edge": make_edge,
            "firefox": make_firefox
        }

        if browser:
            if browser not in browsers:
                raise RuntimeError(
                    "SELENIUM_BROWSER must be one of: "
                    "chrome, edge, firefox"
                )

            return browsers[browser]()

        last_error = None

        for make_browser in (
            make_chrome,
            make_edge,
            make_firefox
        ):
            try:
                return make_browser()

            except Exception as error:
                last_error = error

        raise RuntimeError(
            "Could not start Chrome, Edge, or Firefox "
            "for Selenium tests."
        ) from last_error

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

        self.browser_profile_dir = os.path.join(
            self.temp_dir,
            "browser-profile"
        )

        os.environ["SE_CACHE_PATH"] = os.path.join(
            self.temp_dir,
            "selenium-cache"
        )

        self.db_path = os.path.join(
            self.temp_dir,
            "test.db"
        )

        project_root = Path(__file__).resolve().parents[2]

        self.app = Flask(
            __name__,
            template_folder=str(
                project_root / "app" / "templates"
            ),
            static_folder=str(
                project_root / "app" / "static"
            ),
        )

        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret-key"

        self.app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"sqlite:///{self.db_path}"
        )

        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

        db.init_app(self.app)
        csrf.init_app(self.app)
        login.init_app(self.app)

        login.login_view = "main.signin"

        self.app.register_blueprint(main_bp)

        @self.app.context_processor
        def inject_globals():
            from flask import session
            from app.models import User as UserModel

            username = session.get("user")

            user = (
                UserModel.query
                .filter_by(username=username)
                .first()
                if username else None
            )

            return {
                "logout_form": LogoutForm(),
                "current_user": user
            }

        with self.app.app_context():
            db.create_all()

        self.server = LiveServerThread(self.app)
        self.server.start()

        self.base_url = (
            f"http://{self.server.host}:{self.server.port}"
        )

        self.driver = self.create_webdriver()

        self.wait = WebDriverWait(
            self.driver,
            10
        )