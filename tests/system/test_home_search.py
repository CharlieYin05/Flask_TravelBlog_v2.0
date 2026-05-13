import os
import shutil
import tempfile
import unittest
from pathlib import Path

from flask import Flask

from app.extensions import csrf, db, login
from app.forms import LogoutForm
from app.models import User
from app.routes import main_bp
from datetime import datetime
from werkzeug.security import generate_password_hash

from app.models import Itinerary, ItineraryDay, User

class HomeSearchTests(unittest.TestCase):
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
        def inject_globals():
            from flask import session
            from app.models import User as UserModel

            username = session.get("user")
            user = (
                UserModel.query.filter_by(username=username).first()
                if username else None
            )

            return {
                "logout_form": LogoutForm(),
                "current_user": user
            }

        with self.app.app_context():
            db.create_all()

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.engine.dispose()

        shutil.rmtree(self.temp_dir, ignore_errors=True)

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
        country="Japan",
        user_id=None
    ):
        with self.app.app_context():
            if user_id is None:
                user = User.query.first()
                user_id = user.id

            itinerary = Itinerary(
                title=title,
                country=country,
                trip_types=["adventure"],
                user_id=user_id,
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

            return itinerary.id

    def test_homepage_loads_with_hero_text(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Discover, Plan", response.data)

    # Unauthenticated visitors should see Sign in and Sign up links.
    def test_homepage_unauthenticated_shows_auth_links(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sign in", response.data)
        self.assertIn(b"Sign up", response.data)

    def test_search_page_loads_with_input(self):
        response = self.client.get("/search")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"search-input", response.data)
