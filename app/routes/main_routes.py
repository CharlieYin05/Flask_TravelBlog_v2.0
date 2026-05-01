import re

from flask import Blueprint, jsonify, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User


main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("home-page.html")

@main_bp.route("/search")
def search():
    return render_template("search.html")


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
        db.session.commit()

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

        itinerary_data = {
            "user": session.get("user"),
            "trip_title": trip_title,
            "trip_country": trip_country,
            "total_days": total_days,
            "declared_total_days": declared_total_days,
            "trip_types": trip_types,
            "budget_level": request.form.get("budget_level", "").strip(),
            "budget_range": request.form.get("budget_range", "").strip(),
            "cover_photo": {
                "filename": cover_photo.filename,
                "content_type": cover_photo.content_type,
            } if cover_photo and cover_photo.filename else None,
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
                activity_data = {
                    "activity_number": activity_number,
                    "title": request.form.get(title_key, "").strip(),
                    "place": request.form.get(place_key, "").strip(),
                    "time": request.form.get(time_key, "").strip(),
                    "description": request.form.get(description_key, "").strip(),
                    "photo": {
                        "filename": activity_photo.filename,
                        "content_type": activity_photo.content_type,
                    } if activity_photo and activity_photo.filename else None,
                }
                day_data["activities"].append(activity_data)
                activity_number += 1

            itinerary_data["days"].append(day_data)

        print("Received itinerary data:")
        print(itinerary_data)

        return redirect(url_for("main.index"))

    return render_template("Submit-form-page.html")

