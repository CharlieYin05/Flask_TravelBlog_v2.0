import re

from flask import Blueprint, jsonify, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import Itinerary, User


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
        from app.models import User, Itinerary
        from app.extensions import db

        # ⭐ 先简单获取数据（避免复杂bug）
        trip_title = request.form.get("trip_title", "").strip()
        trip_country = request.form.get("trip_country", "").strip()
        trip_types = request.form.getlist("trip_type")
        total_days = request.form.get("total_days", "1")

        # ⭐ 获取用户
        user = User.query.filter_by(username=session.get("user")).first()

        print("USER:", user)

        # ⭐ 创建最小 Itinerary
        itinerary = Itinerary(
            title=trip_title or "Test Title",
            country=trip_country or "Australia",
            trip_types=trip_types if trip_types else ["test"],
            total_days=int(total_days) if total_days.isdigit() else 1,
            budget_level=request.form.get("budget_level") or "test",
            budget_range=request.form.get("budget_range") or "0",
            user_id=user.id
        )

        db.session.add(itinerary)

        try:
            db.session.commit()
            print("COMMIT SUCCESS")
        except Exception as e:
            print("COMMIT ERROR:", e)

        # ⭐ 跳转到 browse（更好测试）
        return redirect(url_for("main.browse"))

    return render_template("Submit-form-page.html")
#最小化，明天提交测试。