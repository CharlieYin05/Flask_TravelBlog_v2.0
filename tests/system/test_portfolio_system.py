import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

from app.extensions import csrf, db, login
from app.forms import LogoutForm
from app.models import Itinerary, ItineraryFavorite, User
from app.routes import main_bp

# Run a temporary Flask server in the background for Selenium to visit.
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

  # End-to-end portfolio page tests that use a real browser.
class PortfolioSystemTests(unittest.TestCase):
    # Helper to create a Selenium webdriver based on environment or availability.
    def create_webdriver(self):
        browser = os.environ.get("SELENIUM_BROWSER", "").lower().strip()
 
        def make_chrome():
            options = ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1400,1000")
            return webdriver.Chrome(options=options)
 
        def make_edge():
            options = EdgeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1400,1000")
            return webdriver.Edge(options=options)
 
        def make_firefox():
            options = FirefoxOptions()
            options.add_argument("--headless")
            return webdriver.Firefox(options=options)
 
        browsers = {
            "chrome": make_chrome,
            "edge": make_edge,
            "firefox": make_firefox,
        }
 
        if browser:
            if browser not in browsers:
                raise RuntimeError(
                    "SELENIUM_BROWSER must be one of: chrome, edge, firefox"
                )
            return browsers[browser]()
 
        last_error = None
 
        for make_browser in (make_chrome, make_edge, make_firefox):
            try:
                return make_browser()
            except Exception as error:
                last_error = error
 
        raise RuntimeError(
            "Could not start Chrome, Edge, or Firefox for Selenium tests. "
            "Install one supported browser, or set SELENIUM_BROWSER=chrome/edge/firefox."
        ) from last_error
    
    # Build a temporary app, database, live server, and browser for each test.
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        project_root = Path(__file__).resolve().parents[2]

        self.app = Flask(
            __name__,
            template_folder=str(project_root / "app" / "templates"),
            static_folder=str(project_root / "app" / "static"),
        )
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret-key"
        self.app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.db_path}"
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["WTF_CSRF_ENABLED"] = False

        db.init_app(self.app)
        csrf.init_app(self.app)
        login.init_app(self.app)
        login.login_view = "main.signin"
        self.app.register_blueprint(main_bp)

        @self.app.context_processor
        def inject_logout_form():
            return {"logout_form": LogoutForm()}

        with self.app.app_context():
            db.create_all()

        self.server = LiveServerThread(self.app)
        self.server.start()
        self.base_url = f"http://{self.server.host}:{self.server.port}"

        self.driver = self.create_webdriver()
        self.wait = WebDriverWait(self.driver, 10)

    # Close the browser and delete all temporary test data.
    def tearDown(self):
        self.driver.quit()
        self.server.shutdown()

        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

        shutil.rmtree(self.temp_dir, ignore_errors=True)

 # Insert a user directly into the test database.
    def create_user(self, username="testuser", email="test@example.com", password="password123"):
        with self.app.app_context():
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()

    # Insert an itinerary for a given user.
    def create_itinerary(self, user_id, title="Test Trip", country="Canada"):
        with self.app.app_context():
            it = Itinerary(
                title=title,
                country=country,
                trip_types=["city"],
                user_id=user_id,
                total_days=2,
                budget_level="$",
                budget_range="$200",
            )
            db.session.add(it)
            db.session.commit()
            return it.id
        
    # Insert a favourite link between a user and an itinerary.
    def create_favourite(self, user_id, itinerary_id):
        with self.app.app_context():
            fav = ItineraryFavorite(user_id=user_id, itinerary_id=itinerary_id)
            db.session.add(fav)
            db.session.commit()

    