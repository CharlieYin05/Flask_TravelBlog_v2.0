import re
from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint, jsonify, render_template,
    request, redirect, session, url_for, current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Itinerary, User, ItineraryDay, ItineraryActivity
#---------------
COVER_UPLOAD_DIR = Path("uploads/cover_photos")
ACTIVITY_UPLOAD_DIR = Path("uploads/activity_photos")

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_image_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_uploaded_file(file, upload_dir: Path):
    if not file or file.filename == "":
        return None

    if not allowed_image_file(file.filename):
        return None

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{ext}"

    upload_path = Path(current_app.static_folder) / upload_dir
    upload_path.mkdir(parents=True, exist_ok=True)

    file_path = upload_path / filename
    file.save(file_path)

    return str(upload_dir / filename)
#---------------
main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("home-page.html")

@main_bp.route("/search")
def search():
    return render_template("search.html")

@main_bp.route("/browse")
def browse():
    itineraries = Itinerary.query.all()
    return render_template("browse-itinerary.html", itineraries=itineraries)


@main_bp.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        error_message = "Incorrect username or password."
        is_ajax_request = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        user = User.query.filter_by(username=username).first()
        if user is None:
            if is_ajax_request:
                return jsonify({"success": False, "error": error_message}), 401
            return render_template("sign-in.html", error=error_message)

        if not check_password_hash(user.password_hash, password):
            if is_ajax_request:
                return jsonify({"success": False, "error": error_message}), 401
            return render_template("sign-in.html", error=error_message)

        session["user"] = user.username
        redirect_url = url_for("main.index")

        if is_ajax_request:
            return jsonify({"success": True, "redirect_url": redirect_url})

        return redirect(redirect_url)

    return render_template("sign-in.html")

@main_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm-password", "")
        is_ajax_request = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if password != confirm_password:
            if is_ajax_request:
                return jsonify({"success": False, "error": "Passwords do not match."}), 400
            return render_template("sign-up.html", error="Passwords do not match.")

        existing_user = User.query.filter_by(username=username).first()
        if existing_user is not None:
            if is_ajax_request:
                return jsonify({"success": False, "error": "This username is already taken."}), 400
            return render_template("sign-up.html", error="This username is already taken.")

        existing_email = User.query.filter_by(email=email).first()
        if existing_email is not None:
            if is_ajax_request:
                return jsonify({"success": False, "error": "This email is already registered."}), 400
            return render_template("sign-up.html", error="This email is already registered.")

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        try:
            db.session.commit()
            print("COMMIT SUCCESS")
        except Exception as e:
            print("COMMIT ERROR:", e)

        redirect_url = url_for("main.signin")

        if is_ajax_request:
            return jsonify({"success": True, "redirect_url": redirect_url})

        return redirect(redirect_url)

    return render_template("sign-up.html")


@main_bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("main.signin"))


@main_bp.route("/submit", methods=["GET", "POST"])
def submit_itinerary():
    if not session.get("user"):
        return redirect(url_for("main.signin"))
    
    if request.method == "POST":
        current_user = User.query.filter_by(username=session.get("user")).first()
        if current_user is None:
            return redirect(url_for("main.signin"))

        trip_title = request.form.get("trip_title", "").strip()
        trip_country = request.form.get("trip_country", "").strip()
        total_days_raw = request.form.get("total_days", "0").strip()
        declared_total_days = int(total_days_raw) if total_days_raw.isdigit() else 0

        cover_photo = request.files.get("cover_photo")
        trip_types = request.form.getlist("trip_type")

        day_numbers = set()
        day_key_pattern = re.compile(r"day(\d+)")

        for key in list(request.form.keys()) + list(request.files.keys()):
            match = day_key_pattern.search(key)
            if match:
                day_numbers.add(int(match.group(1)))

        inferred_total_days = max(day_numbers) if day_numbers else 0
        total_days = max(declared_total_days, inferred_total_days)

        cover_photo_path = save_uploaded_file(cover_photo, COVER_UPLOAD_DIR)

        itinerary_data = {
            "user": session.get("user"),
            "trip_title": trip_title,
            "trip_country": trip_country,
            "total_days": total_days,
            "declared_total_days": declared_total_days,
            "trip_types": trip_types,
            "budget_level": request.form.get("budget_level", "").strip(),
            "budget_range": request.form.get("budget_range", "").strip(),
            "cover_photo_path": cover_photo_path,
            "days": [],
        }

        for day_number in range(1, total_days + 1):
            day_data = {
                "day_number": day_number,
                "state": request.form.get(f"state_day{day_number}", "").strip(),
                "city": request.form.get(f"city_day{day_number}", "").strip(),
                "transport": request.form.getlist(f"transport_day{day_number}[]"),
                "transport_other_text": request.form.get(
                    f"transport_other_text_day{day_number}", ""
                ).strip(),
                "restaurants": request.form.getlist(f"restaurant_dropdown_day{day_number}"),
                "restaurant_specific": request.form.get(
                    f"restaurant_specific_day{day_number}", ""
                ).strip(),
                "accommodations": request.form.getlist(f"accommodation_dropdown_day{day_number}"),
                "accommodation_specific": request.form.get(
                    f"accommodation_specific_day{day_number}", ""
                ).strip(),
                "activities": [],
            }

            activity_number = 1
            while True:
                title_key = f"activity_title_day{day_number}_{activity_number}"
                place_key = f"activity_place_day{day_number}_{activity_number}"
                time_key = f"time_day{day_number}_{activity_number}"
                description_key = f"activity_day{day_number}_{activity_number}"
                photo_key = f"activity_photo_day{day_number}_{activity_number}"

                has_activity_fields = any(
                    key in request.form or key in request.files
                    for key in (title_key, place_key, time_key, description_key, photo_key)
                )

                if not has_activity_fields:
                    break

                activity_photo = request.files.get(photo_key)
                activity_photo_path = save_uploaded_file(
                    activity_photo,
                    ACTIVITY_UPLOAD_DIR,
                )
                activity_data = {
                    "activity_number": activity_number,
                    "title": request.form.get(title_key, "").strip(),
                    "place": request.form.get(place_key, "").strip(),
                    "time": request.form.get(time_key, "").strip(),
                    "description": request.form.get(description_key, "").strip(),
                    "photo_path": activity_photo_path,
                }
                day_data["activities"].append(activity_data)
                activity_number += 1

            itinerary_data["days"].append(day_data)

        itinerary = Itinerary(
            title=itinerary_data["trip_title"],
            country=itinerary_data["trip_country"],
            trip_types=itinerary_data["trip_types"],
            user_id=current_user.id,
            cover_image_url=itinerary_data["cover_photo_path"],
            total_days=itinerary_data["total_days"],
            budget_level=itinerary_data["budget_level"],
            budget_range=itinerary_data["budget_range"],
        )

        for day in itinerary_data["days"]:
            itinerary_day = ItineraryDay(
                day_number=day["day_number"],
                state=day["state"] or None,
                city=day["city"] or None,
                transport=day["transport"],
                transport_other_text=day["transport_other_text"] or None,
                restaurants=day["restaurants"],
                restaurant_specific=day["restaurant_specific"] or None,
                accommodations=day["accommodations"],
                accommodation_specific=day["accommodation_specific"] or None,
            )

            for activity in day["activities"]:
                itinerary_activity = ItineraryActivity(
                    activity_name=activity["title"],
                    place=activity["place"] or None,
                    time=activity["time"] or None,
                    description=activity["description"] or None,
                    photo_url=activity["photo_path"],
                )
                itinerary_day.activities.append(itinerary_activity)

            itinerary.days.append(itinerary_day)

        db.session.add(itinerary)
        db.session.commit()

        return redirect(url_for("main.browse"))

    return render_template("Submit-form-page.html")