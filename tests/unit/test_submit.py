import os
import shutil
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from flask import Flask
from werkzeug.security import generate_password_hash

from app.extensions import csrf, db, login
from app.forms import LogoutForm
from app.models import User
from app.routes import main_bp

# Build an isolated app + database so submit tests do not touch dev data.
class SubmitTests(unittest.TestCase):
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

        self.client = self.app.test_client()
        self.create_user()

    # Clean up the temporary database after each test.
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # Helper for tests that require a signed-in user.
    def create_user(self):
        with self.app.app_context():
            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=generate_password_hash("password123"),
            )
            db.session.add(user)
            db.session.commit()

    # Put the test user into session so the submit route treats us as logged in.
    def login_user(self):
        with self.app.app_context():
            user = User.query.filter_by(username="testuser").first()

        with self.client.session_transaction() as session:
            session["_user_id"] = str(user.id)
            session["_fresh"] = True

    # Build a small in-memory image upload for form submission tests.
    def image_upload(self, filename="test.png"):
        return (BytesIO(b"fake image bytes"), filename)

    # This is the smallest valid itinerary payload for one day and one activity
    def valid_submit_data(self):
        return {
            "trip_title": "Perth Weekend",
            "trip_country": "Australia",
            "total_days": "1",
            "trip_type": "city",
            "cover_photo": self.image_upload("cover.png"),
            "budget_level": "$$",
            "budget_range": "$500-$800",
            "state_day1": "WA",
            "city_day1": "Perth",
            "transport_day1[]": "flight",
            "restaurant_dropdown_day1": "Cafe",
            "accommodation_dropdown_day1": "Hotel",
            "activity_title_day1_1": "Kings Park Visit",
            "activity_place_day1_1": "Kings Park",
            "activity_photo_day1_1": self.image_upload("activity.png"),
            "time_day1_1": "09:00",
            "activity_day1_1": "Walk around the park and city lookout.",
        }

    # Guests should be redirected to signin before they can open the submit page
    def test_submit_requires_login(self):
        response = self.client.get("/submit", follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/signin", response.headers["Location"])

    # Logged-in users should see an error if the trip title is missing.
    def test_submit_missing_title(self):
        self.login_user()
        data = self.valid_submit_data()
        data["trip_title"] = ""

        response = self.client.post("/submit", data=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Trip title is required.", response.data)

    # Each day needs a city, so removing it should trigger validation.
    def test_submit_missing_city(self):
        self.login_user()
        data = self.valid_submit_data()
        data["city_day1"] = ""

        response = self.client.post("/submit", data=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"City is required for Day 1.", response.data)

    # Activities exist, but an empty title should still fail validation.
    def test_submit_missing_activity_title(self):
        self.login_user()
        data = self.valid_submit_data()
        data["activity_title_day1_1"] = ""

        response = self.client.post("/submit", data=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Activity title is required for Day 1, Activity 1.", response.data)

    # A valid itinerary should be accepted and redirect to the browse page.
    def test_submit_success(self):
        self.login_user()
        response = self.client.post("/submit", data=self.valid_submit_data(), follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/browse", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
