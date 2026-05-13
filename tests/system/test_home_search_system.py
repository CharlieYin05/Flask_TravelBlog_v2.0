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
from datetime import datetime
from werkzeug.security import generate_password_hash

from app.models import Itinerary, ItineraryDay, User

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
    def tearDown(self):
        self.driver.quit()

        self.server.shutdown()

        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

        shutil.rmtree(
            self.temp_dir,
            ignore_errors=True
        )

    def create_user(
        self,
        username="testuser",
        email="test@example.com",
        password="password123"
    ):
        with self.app.app_context():
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
            )

            db.session.add(user)
            db.session.commit()

            return user.id

    def create_itinerary(
        self,
        title="Tokyo Adventure",
        country="Japan"
    ):
        with self.app.app_context():
            user = User.query.first()

            itinerary = Itinerary(
                title=title,
                country=country,
                trip_types=["adventure"],
                user_id=user.id,
                cover_image_url="uploads/cover_photos/test.png",
                total_days=3,
                budget_level="$$",
                budget_range="$1000-$1500",
                created_at=datetime.utcnow(),
            )

            day = ItineraryDay(
                day_number=1,
                state="Tokyo",
                city="Shinjuku",
                transport=["train"],
                restaurants=["Ramen Bar"],
                accommodations=["Hostel"],
            )

            itinerary.days.append(day)

            db.session.add(itinerary)
            db.session.commit()


    # The homepage hero heading should be visible on load.
    def test_homepage_hero_heading_visible(self):
        self.driver.get(self.base_url)

        heading = self.wait.until(
            EC.visibility_of_element_located(
                (By.TAG_NAME, "h1")
            )
        )

        self.assertIn(
            "Discover, Plan",
            heading.text
        )

    # The three "How it works" cards should all be present.
    def test_homepage_how_it_works_cards_visible(self):
        self.driver.get(self.base_url)

        self.wait.until(
            EC.visibility_of_element_located(
                (By.TAG_NAME, "h2")
            )
        )

        page = self.driver.page_source

        self.assertIn("Explore", page)
        self.assertIn("Share", page)
        self.assertIn("Plan", page)

    # The search page should render the search input field.
    def test_search_page_input_is_present(self):
        self.driver.get(f"{self.base_url}/search")

        search_input = self.wait.until(
            EC.visibility_of_element_located(
                (By.ID, "search-input")
            )
        )

        self.assertTrue(
            search_input.is_displayed()
        )

    # Clicking "By Country" should activate the button.
    def test_search_country_toggle_becomes_active(self):
        self.driver.get(f"{self.base_url}/search")

        country_btn = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "toggle-country")
            )
        )

        country_btn.click()

        classes = country_btn.get_attribute("class")

        self.assertIn("bg-white", classes)
        self.assertIn("text-indigo-600", classes)

    # Typing a query should render matching result cards.
    def test_search_returns_results_for_matching_query(self):
        self.create_user()

        self.create_itinerary(
            title="Tokyo Adventure",
            country="Japan"
        )

        self.driver.get(
            f"{self.base_url}/search"
        )

        search_input = self.wait.until(
            EC.element_to_be_clickable(
                (By.ID, "search-input")
            )
        )

        search_input.send_keys("Tokyo")

        result = self.wait.until(
            EC.visibility_of_element_located(
                (By.CLASS_NAME, "result-box")
            )
        )

        self.assertIn(
            "Tokyo Adventure",
            self.driver.find_element(
                By.ID,
                "search-results"
            ).text
        )

if __name__ == "__main__":
    unittest.main()