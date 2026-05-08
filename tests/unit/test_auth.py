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

# Build an isolated app + database so auth tests do not touch dev data.
class AuthTests(unittest.TestCase):
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

        self.client = self.app.test_client()

    # Clean up the temporary database after each test.
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # Helper for tests that need an existing account in the database.
    def create_user(self, username="existinguser", email="existing@example.com", password="password123"):
        with self.app.app_context():
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()

    # Signup should reject users when the two passwords do not match.
    def test_signup_password_mismatch(self):
        response = self.client.post(
            "/signup",
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "confirm-password": "different123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Passwords do not match.", response.data)

    # Signup should validate email format before creating the user.
    def test_signup_invalid_email(self):
        response = self.client.post(
            "/signup",
            data={
                "username": "newuser",
                "email": "not-an-email",
                "password": "password123",
                "confirm-password": "password123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please enter a valid email address.", response.data)

    # Signup should block reuse of an existing username.
    def test_signup_duplicate_username(self):
        self.create_user()

        response = self.client.post(
            "/signup",
            data={
                "username": "existinguser",
                "email": "another@example.com",
                "password": "password123",
                "confirm-password": "password123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"This username is already taken.", response.data)

    # A valid signup should redirect to signin and store the new user.
    def test_signup_success(self):
        response = self.client.post(
            "/signup",
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "confirm-password": "password123",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/signin", response.headers["Location"])

        with self.app.app_context():
            user = User.query.filter_by(username="newuser").first()
            self.assertIsNotNone(user)

    # Signin should show an error when the password is incorrect.
    def test_signin_wrong_password(self):
        self.create_user(password="correctpassword")

        response = self.client.post(
            "/signin",
            data={
                "username": "existinguser",
                "password": "wrongpassword",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Incorrect username or password.", response.data)


if __name__ == "__main__":
    unittest.main()
