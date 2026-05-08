import os
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

from app.extensions import db
from app.models import User
from app.routes import main_bp


# Run a temporary Flask server in the background for Selenium to visit.
class LiveServerThread(threading.Thread):
    # Start a local WSGI server on a free port.
    def __init__(self, app, host="127.0.0.1", port=0):
        super().__init__(daemon=True)
        self.server = make_server(host, port, app)
        self.host = host
        self.port = self.server.server_port
        self.context = app.app_context()
        self.context.push()

    # Keep serving requests until the test finishes.
    def run(self):
        self.server.serve_forever()

    # Stop the server and release the app context.
    def shutdown(self):
        self.server.shutdown()
        self.context.pop()


# End-to-end auth tests that use a real browser.
class AuthSystemTests(unittest.TestCase):
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

        db.init_app(self.app)
        self.app.register_blueprint(main_bp)

        with self.app.app_context():
            db.create_all()

        # Start a real local server so Selenium can interact with the app in a browser.
        self.server = LiveServerThread(self.app)
        self.server.start()
        self.base_url = f"http://{self.server.host}:{self.server.port}"

        # Edge matches the course setup and Selenium can manage the driver automatically.
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1400,1000")
        self.driver = webdriver.Edge(options=options)
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

    # Insert a user directly into the test database for login scenarios.
    def create_user(
        self,
        username="existinguser",
        email="existing@example.com",
        password="password123",
    ):
        with self.app.app_context():
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()

    # Reuse the signin form steps across multiple browser tests.
    def fill_signin_form(self, username, password):
        self.driver.find_element(By.ID, "username").clear()
        self.driver.find_element(By.ID, "username").send_keys(username)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.ID, "login-button").click()

    # A user can sign up successfully and gets sent back to the signin page.
    def test_signup_system(self):
        self.driver.get(f"{self.base_url}/signup")

        self.driver.find_element(By.ID, "username").send_keys("newuser")
        self.driver.find_element(By.ID, "email").send_keys("newuser@example.com")
        self.driver.find_element(By.ID, "password").send_keys("password123")
        self.driver.find_element(By.ID, "confirm-password").send_keys("password123")
        self.driver.find_element(By.ID, "signup-button").click()

        self.wait.until(EC.url_contains("/signin"))
        self.assertIn("/signin", self.driver.current_url)
        self.assertIn("Sign In", self.driver.page_source)

    # Wrong credentials should keep the user on signin and show an error.
    def test_signin_system_wrong_password(self):
        self.create_user(password="correctpassword")
        self.driver.get(f"{self.base_url}/signin")

        self.fill_signin_form("existinguser", "wrongpassword")

        error = self.wait.until(EC.visibility_of_element_located((By.ID, "signin-error")))
        self.assertIn("Incorrect username or password.", error.text)

    # Correct credentials should take the user to the home page.
    def test_signin_system_success(self):
        self.create_user(password="correctpassword")
        self.driver.get(f"{self.base_url}/signin")

        self.fill_signin_form("existinguser", "correctpassword")

        self.wait.until(EC.url_to_be(f"{self.base_url}/"))
        heading = self.wait.until(
            EC.visibility_of_element_located((By.TAG_NAME, "h1"))
        )
        self.assertIn("Discover, Plan", heading.text)

    # Signed-in users can log out and return to the logged-out home page.
    def test_logout_system(self):
        self.create_user(password="correctpassword")
        self.driver.get(f"{self.base_url}/signin")

        self.fill_signin_form("existinguser", "correctpassword")
        self.wait.until(EC.url_to_be(f"{self.base_url}/"))

        sign_out_link = self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Sign out"))
        )
        sign_out_link.click()
        self.wait.until(EC.url_to_be(f"{self.base_url}/"))

        self.assertEqual(self.driver.current_url, f"{self.base_url}/")
        self.assertIn("Sign in", self.driver.page_source)


if __name__ == "__main__":
    unittest.main()
