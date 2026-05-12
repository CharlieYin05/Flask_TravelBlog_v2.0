import os
import shutil
import tempfile
import unittest
from pathlib import Path

from flask import Flask
from werkzeug.security import generate_password_hash

from app.extensions import csrf, db, login
from app.forms import LogoutForm
from app.models import (
    Itinerary,
    ItineraryActivity,
    ItineraryComment,
    ItineraryDay,
    User,
)
from app.routes import main_bp


# Build an isolated app + database so browse/view tests do not touch dev data.
class BrowseViewTests(unittest.TestCase):
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

    # Helper for tests that need an existing user.
    def create_user(
        self,
        username="testuser",
        email="test@example.com",
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
            return user.id

    # Put a user into session so protected interaction APIs treat us as logged in.
    def login_user(self, username="testuser"):
        with self.app.app_context():
            user = User.query.filter_by(username=username).first()

        with self.client.session_transaction() as session:
            session["_user_id"] = str(user.id)
            session["_fresh"] = True

    # Create a full itinerary with one day and one activity.
    def create_itinerary(self, title="Perth Weekend", country="Australia"):
        with self.app.app_context():
            user = User.query.filter_by(username="testuser").first()

            itinerary = Itinerary(
                title=title,
                country=country,
                trip_types=["city", "food-centric"],
                user_id=user.id,
                cover_image_url="uploads/cover_photos/test-cover.png",
                total_days=1,
                budget_level="$$",
                budget_range="$500-$800",
            )

            day = ItineraryDay(
                day_number=1,
                state="WA",
                city="Perth",
                transport=["walk", "train"],
                restaurants=["Cafe"],
                accommodations=["Hotel"],
            )

            activity = ItineraryActivity(
                activity_name="Kings Park Visit",
                place="Kings Park",
                time="09:00",
                description="Walk around the park and city lookout.",
                photo_url="uploads/activity_photos/test-activity.png",
            )

            day.activities.append(activity)
            itinerary.days.append(day)

            db.session.add(itinerary)
            db.session.commit()

            return itinerary.id

    # Browse should show itinerary cards when itineraries exist.
    def test_browse_page_lists_itineraries(self):
        self.create_itinerary()

        response = self.client.get("/browse")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Perth Weekend", response.data)
        self.assertIn(b"Australia", response.data)
        self.assertIn(b"testuser", response.data)
        self.assertIn(b"city", response.data)

    # Browse should show an empty state when there are no itineraries.
    def test_browse_page_empty_state(self):
        response = self.client.get("/browse")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No itineraries yet", response.data)
        self.assertIn(b"Create Itinerary", response.data)

    # The browse API should return itinerary data as JSON.
    def test_api_itineraries_returns_json(self):
        itinerary_id = self.create_itinerary()

        response = self.client.get("/api/itineraries")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], itinerary_id)
        self.assertEqual(data[0]["title"], "Perth Weekend")
        self.assertEqual(data[0]["country"], "Australia")
        self.assertEqual(data[0]["days"], 1)

    # A valid itinerary detail page should render the view page shell.
    def test_view_page_loads_for_existing_itinerary(self):
        itinerary_id = self.create_itinerary()

        response = self.client.get(f"/itinerary/{itinerary_id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Daily Timeline", response.data)
        self.assertIn(b"Google Map", response.data)
        self.assertIn(b'id="like-btn"', response.data)
        self.assertIn(b'id="comment-box"', response.data)

    # Missing itinerary detail pages should return 404.
    def test_view_page_404_for_missing_itinerary(self):
        response = self.client.get("/itinerary/99999")

        self.assertEqual(response.status_code, 404)

    # The detail API should return nested day and activity data for the view page.
    def test_api_itinerary_returns_full_nested_data(self):
        itinerary_id = self.create_itinerary()

        response = self.client.get(f"/api/itinerary/{itinerary_id}")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["title"], "Perth Weekend")
        self.assertEqual(data["country"], "Australia")
        self.assertEqual(data["author"], "testuser")
        self.assertIn("city", data["tags"])
        self.assertEqual(data["overview"], "1 days itinerary in Australia.")
        self.assertEqual(len(data["days"]), 1)
        self.assertEqual(data["days"][0]["city"], "Perth")
        self.assertEqual(data["days"][0]["activities"][0]["title"], "Kings Park Visit")
        self.assertEqual(data["days"][0]["activities"][0]["place"], "Kings Park")

    # Guests should not be allowed to like an itinerary.
    def test_unauthenticated_like_is_rejected(self):
        itinerary_id = self.create_itinerary()

        response = self.client.post(f"/api/itinerary/{itinerary_id}/like")
        data = response.get_json()

        self.assertEqual(response.status_code, 401)
        self.assertFalse(data["success"])
        self.assertIn("/signin", data["redirect_url"])

    # Empty comments should be rejected even when the user is logged in.
    def test_empty_comment_is_rejected(self):
        itinerary_id = self.create_itinerary()
        self.login_user()

        response = self.client.post(
            f"/api/itinerary/{itinerary_id}/comments",
            json={"content": "   "},
        )
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Comment cannot be empty.")

    # A user should not be able to delete another user's comment.
    def test_user_cannot_delete_another_users_comment(self):
        itinerary_id = self.create_itinerary()

        with self.app.app_context():
            owner = User.query.filter_by(username="testuser").first()

            other_user = User(
                username="otheruser",
                email="other@example.com",
                password_hash=generate_password_hash("password123"),
            )
            db.session.add(other_user)
            db.session.commit()

            comment = ItineraryComment(
                itinerary_id=itinerary_id,
                user_id=owner.id,
                content="This is the owner's comment.",
            )
            db.session.add(comment)
            db.session.commit()

            comment_id = comment.id

        self.login_user("otheruser")

        response = self.client.delete(f"/api/itinerary/comments/{comment_id}")
        data = response.get_json()

        self.assertEqual(response.status_code, 403)
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "You can only delete your own comments.")


if __name__ == "__main__":
    unittest.main()
