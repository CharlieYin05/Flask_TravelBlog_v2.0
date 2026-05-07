import re
from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    redirect,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import (
    Itinerary,
    User,
    ItineraryDay,
    ItineraryActivity,
    ItineraryLike,
    ItineraryFavorite,
    ItineraryComment,
)


main_bp = Blueprint("main", __name__)

# Static upload folders
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
COVER_UPLOAD_DIR = STATIC_DIR / "uploads" / "cover_photos"
ACTIVITY_UPLOAD_DIR = STATIC_DIR / "uploads" / "activity_photos"

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_image_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )


def save_uploaded_file(file_storage, upload_dir: Path):
    if not file_storage or not file_storage.filename:
        return None

    if not allowed_image_file(file_storage.filename):
        return None

    upload_dir.mkdir(parents=True, exist_ok=True)

    original_filename = secure_filename(file_storage.filename)
    ext = original_filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{ext}"

    save_path = upload_dir / filename
    file_storage.save(save_path)

    return str(save_path.relative_to(STATIC_DIR)).replace("\\", "/")


def get_current_user():
    username = session.get("user")
    if not username:
        return None
    return User.query.filter_by(username=username).first()


def require_login_json():
    current_user = get_current_user()
    if current_user is None:
        return None, (jsonify({
            "success": False,
            "error": "Please sign in to use this feature.",
            "redirect_url": url_for("main.signin"),
        }), 401)
    return current_user, None


@main_bp.route("/")
def index():
    return render_template("home-page.html")


@main_bp.route("/search", methods=["GET"])
def search():
    return render_template("search.html")


@main_bp.route("/api/search", methods=["GET"])
def search_api():
    query = request.args.get('query', '').strip()
    results = []
    
    if query:
        results = Itinerary.query.filter(
            Itinerary.title.ilike(f'%{query}%')
        ).all()
    
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'country': r.country,
        'cover_image_url': r.cover_image_url,
        'total_days': r.total_days
    } for r in results])


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
            password_hash=generate_password_hash(password),
        )

        db.session.add(new_user)

        try:
            db.session.commit()
            print("COMMIT SUCCESS")
        except Exception as e:
            db.session.rollback()
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
                "restaurants": request.form.getlist(
                    f"restaurant_dropdown_day{day_number}"
                ),
                "restaurant_specific": request.form.get(
                    f"restaurant_specific_day{day_number}", ""
                ).strip(),
                "accommodations": request.form.getlist(
                    f"accommodation_dropdown_day{day_number}"
                ),
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
                    for key in (
                        title_key,
                        place_key,
                        time_key,
                        description_key,
                        photo_key,
                    )
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
            title=itinerary_data["trip_title"] or "Untitled Trip",
            country=itinerary_data["trip_country"] or "Unknown",
            trip_types=itinerary_data["trip_types"],
            user_id=current_user.id,
            cover_image_url=itinerary_data["cover_photo_path"],
            total_days=itinerary_data["total_days"],
            budget_level=itinerary_data["budget_level"] or "Not specified",
            budget_range=itinerary_data["budget_range"] or "Not specified",
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
                    activity_name=activity["title"] or "Untitled Activity",
                    place=activity["place"] or None,
                    time=activity["time"] or None,
                    description=activity["description"] or None,
                    photo_url=activity["photo_path"],
                )

                itinerary_day.activities.append(itinerary_activity)

            itinerary.days.append(itinerary_day)

        db.session.add(itinerary)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("COMMIT ERROR:", e)
            raise

        return redirect(url_for("main.browse"))

    return render_template("Submit-form-page.html")

#Browse itineraries page (can fetch data)
@main_bp.route("/api/itineraries")
def get_itineraries():
    itineraries = Itinerary.query.all()

    data = []
    for it in itineraries:
        data.append({
            "id": it.id,
            "title": it.title,
            "country": it.country,
            "cover": it.cover_image_url,
            "days": it.total_days,
        })

    return jsonify(data)

# View itinerary details page (placeholder, can be expanded later)
@main_bp.route("/api/itinerary/<int:id>")
def get_itinerary(id):
    it = Itinerary.query.get_or_404(id)

    result = {
        "title": it.title,
        "country": it.country,
        "author": it.user.username if it.user else "Unknown",
        "date": "",
        "tags": it.trip_types or [],
        "overview": f"{it.total_days} days itinerary in {it.country}.",
        "coverPhoto": "/static/" + it.cover_image_url if it.cover_image_url else "",
        "days": []
    }

    for day in it.days:
        day_data = {
         "day": day.day_number,
         "state": day.state or "",
         "city": day.city or "",
         "transport": day.transport or [],
         "restaurants": day.restaurants or [],
         "restaurant_specific": day.restaurant_specific or "",
          "accommodations": day.accommodations or [],
         "accommodation_specific": day.accommodation_specific or "",
         "activities": []
        }

        for act in day.activities:
            day_data["activities"].append({
                "title": act.activity_name,
                "description": act.description,
                "time": act.time,
                "place": act.place,
                "image": "/static/" + act.photo_url if act.photo_url else ""
            })

        result["days"].append(day_data)

    return jsonify(result)


@main_bp.route("/api/itinerary/<int:id>/interactions", methods=["GET"])
def get_itinerary_interactions(id):
    Itinerary.query.get_or_404(id)
    current_user = get_current_user()

    comments = (
        ItineraryComment.query
        .filter_by(itinerary_id=id)
        .order_by(ItineraryComment.created_at.desc())
        .all()
    )

    return jsonify({
        "like_count": ItineraryLike.query.filter_by(itinerary_id=id).count(),
        "favorite_count": ItineraryFavorite.query.filter_by(itinerary_id=id).count(),
        "comment_count": len(comments),
        "liked_by_me": bool(
            current_user and ItineraryLike.query.filter_by(
                itinerary_id=id,
                user_id=current_user.id,
            ).first()
        ),
        "favorited_by_me": bool(
            current_user and ItineraryFavorite.query.filter_by(
                itinerary_id=id,
                user_id=current_user.id,
            ).first()
        ),
        "comments": [
            {
                "id": comment.id,
                "content": comment.content,
                "author": comment.user.username if comment.user else "Unknown",
                "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for comment in comments
        ],
    })


@main_bp.route("/api/itinerary/<int:id>/like", methods=["POST"])
def toggle_itinerary_like(id):
    Itinerary.query.get_or_404(id)
    current_user, error_response = require_login_json()
    if error_response:
        return error_response

    existing_like = ItineraryLike.query.filter_by(
        itinerary_id=id,
        user_id=current_user.id,
    ).first()

    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        db.session.add(ItineraryLike(itinerary_id=id, user_id=current_user.id))
        liked = True

    db.session.commit()

    return jsonify({
        "success": True,
        "liked_by_me": liked,
        "like_count": ItineraryLike.query.filter_by(itinerary_id=id).count(),
    })


@main_bp.route("/api/itinerary/<int:id>/favorite", methods=["POST"])
def toggle_itinerary_favorite(id):
    Itinerary.query.get_or_404(id)
    current_user, error_response = require_login_json()
    if error_response:
        return error_response

    existing_favorite = ItineraryFavorite.query.filter_by(
        itinerary_id=id,
        user_id=current_user.id,
    ).first()

    if existing_favorite:
        db.session.delete(existing_favorite)
        favorited = False
    else:
        db.session.add(ItineraryFavorite(itinerary_id=id, user_id=current_user.id))
        favorited = True

    db.session.commit()

    return jsonify({
        "success": True,
        "favorited_by_me": favorited,
        "favorite_count": ItineraryFavorite.query.filter_by(itinerary_id=id).count(),
    })


@main_bp.route("/api/itinerary/<int:id>/comments", methods=["POST"])
def create_itinerary_comment(id):
    Itinerary.query.get_or_404(id)
    current_user, error_response = require_login_json()
    if error_response:
        return error_response

    payload = request.get_json(silent=True) or {}
    content = payload.get("content", "").strip()

    if not content:
        return jsonify({"success": False, "error": "Comment cannot be empty."}), 400

    comment = ItineraryComment(
        itinerary_id=id,
        user_id=current_user.id,
        content=content,
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "success": True,
        "comment_count": ItineraryComment.query.filter_by(itinerary_id=id).count(),
        "comment": {
            "id": comment.id,
            "content": comment.content,
            "author": current_user.username,
            "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M"),
        },
    }), 201


# View itinerary details page
@main_bp.route("/itinerary/<int:id>")
def view_itinerary(id):
    itinerary = Itinerary.query.get_or_404(id)
    return render_template("view-itinerary.html", itinerary=itinerary)

# View itinerary page delete own comments
@main_bp.route("/api/itinerary/comments/<int:comment_id>", methods=["DELETE"])
def delete_itinerary_comment(comment_id):
    current_user, error_response = require_login_json()
    if error_response:
        return error_response

    comment = ItineraryComment.query.get_or_404(comment_id)

    if comment.user_id != current_user.id:
        return jsonify({
            "success": False,
            "error": "You can only delete your own comments."
        }), 403

    itinerary_id = comment.itinerary_id

    db.session.delete(comment)
    db.session.commit()

    return jsonify({
        "success": True,
        "comment_count": ItineraryComment.query.filter_by(
            itinerary_id=itinerary_id
        ).count()
    })

# Portfolio page
@main_bp.route("/portfolio")
def portfolio():
    if not session.get("user"):
        return redirect(url_for("main.signin"))
    
    current_user = User.query.filter_by(
        username=session.get("user")
    ).first()
    
    itineraries = Itinerary.query.filter_by(
        user_id=current_user.id
    ).all()
    
    return render_template(
        "portfolio-page.html",
        user=current_user,
        itineraries=itineraries
    )
