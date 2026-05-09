import os
import shutil
import tempfile
import unittest
from pathlib import Path

from flask import Flask
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import User
from app.routes import main_bp


class SubmitTests(unittest.TestCase):
    def setUp(self):
        # Build an isolated app + database so submit tests do not touch dev data.
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

        self.client = self.app.test_client()
        self.create_user()

    def tearDown(self):
        # Clean up the temporary database after each test.
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_user(self):
        # Helper for tests that require a signed-in user.
        with self.app.app_context():
            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=generate_password_hash("password123"),
            )
            db.session.add(user)
            db.session.commit()

    def login_user(self):
        # Put the test user into session so the submit route treats us as logged in.
        with self.client.session_transaction() as session:
            session["user"] = "testuser"

    def valid_submit_data(self):
        # This is the smallest valid itinerary payload for one day and one activity.
        return {
            "trip_title": "Perth Weekend",
            "trip_country": "Australia",
            "total_days": "1",
            "trip_type": "city",
            "budget_level": "$$",
            "budget_range": "$500-$800",
            "state_day1": "WA",
            "city_day1": "Perth",
            "activity_title_day1_1": "Kings Park Visit",
            "activity_place_day1_1": "Kings Park",
            "time_day1_1": "09:00",
            "activity_day1_1": "Walk around the park and city lookout.",
        }

    def test_submit_requires_login(self):
        # Guests should be redirected to signin before they can open the submit page.
        response = self.client.get("/submit", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/signin", response.headers["Location"])

    def test_submit_missing_title(self):
        # Logged-in users should see an error if the trip title is missing.
        self.login_user()
        data = self.valid_submit_data()
        data["trip_title"] = ""

        response = self.client.post("/submit", data=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Trip title is required.", response.data)

    def test_submit_missing_city(self):
        # Each day needs a city, so removing it should trigger validation.
        self.login_user()
        data = self.valid_submit_data()
        data["city_day1"] = ""

        response = self.client.post("/submit", data=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"City is required for Day 1.", response.data)

    def test_submit_missing_activity_title(self):
        # Activities exist, but an empty title should still fail validation.
        self.login_user()
        data = self.valid_submit_data()
        data["activity_title_day1_1"] = ""

        response = self.client.post("/submit", data=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Activity title is required for Day 1, Activity 1.", response.data)

    def test_submit_success(self):
        # A valid itinerary should be accepted and redirect to the browse page.
        self.login_user()
        response = self.client.post("/submit", data=self.valid_submit_data(), follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/browse", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
