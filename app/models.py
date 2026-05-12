from datetime import datetime

from app.extensions import db, login
from werkzeug.security import check_password_hash, generate_password_hash


@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)
    banner_url = db.Column(db.String(255), nullable=True)
    itineraries = db.relationship("Itinerary", back_populates="user")
    likes = db.relationship("ItineraryLike", back_populates="user", cascade="all, delete-orphan")
    favorites = db.relationship("ItineraryFavorite", back_populates="user", cascade="all, delete-orphan")
    comments = db.relationship("ItineraryComment", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Itinerary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(255), nullable=False)
    trip_types = db.Column(db.JSON, nullable=False, default=list)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="itineraries")

    cover_image_url = db.Column(db.String(255), nullable=True)
    total_days = db.Column(db.Integer, nullable=False)  
    budget_level = db.Column(db.String(50), nullable=False)
    budget_range = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    days = db.relationship(
        "ItineraryDay",
        back_populates="itinerary",
        cascade="all, delete-orphan"
    )

    likes = db.relationship("ItineraryLike", back_populates="itinerary", cascade="all, delete-orphan")
    favorites = db.relationship("ItineraryFavorite", back_populates="itinerary", cascade="all, delete-orphan")
    comments = db.relationship("ItineraryComment", back_populates="itinerary", cascade="all, delete-orphan", order_by="ItineraryComment.created_at.desc()")


class ItineraryDay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_number = db.Column(db.Integer, nullable=False)
    state = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(255), nullable=True)
    transport = db.Column(db.JSON, nullable=False, default=list)
    transport_other_text = db.Column(db.String(255), nullable=True)
    restaurants = db.Column(db.JSON, nullable=False, default=list)
    restaurant_specific = db.Column(db.String(255), nullable=True)
    accommodations = db.Column(db.JSON, nullable=False, default=list)
    accommodation_specific = db.Column(db.String(255), nullable=True)

    itinerary_id = db.Column(
        db.Integer,
        db.ForeignKey("itinerary.id"),
        nullable=False
    )
    
    itinerary = db.relationship("Itinerary", back_populates="days")

    activities = db.relationship(
        "ItineraryActivity",
        back_populates="day",
        cascade="all, delete-orphan"
    )

class ItineraryActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_name = db.Column(db.String(255), nullable=False)
    place = db.Column(db.String(255), nullable=True)
    time = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)

    day_id = db.Column(
        db.Integer,
        db.ForeignKey("itinerary_day.id"),
        nullable=False
    )
    day = db.relationship("ItineraryDay", back_populates="activities")


class ItineraryLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    itinerary_id = db.Column(db.Integer, db.ForeignKey("itinerary.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="likes")
    itinerary = db.relationship("Itinerary", back_populates="likes")

    __table_args__ = (
        db.UniqueConstraint("user_id", "itinerary_id", name="uq_user_itinerary_like"),
    )


class ItineraryFavorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    itinerary_id = db.Column(db.Integer, db.ForeignKey("itinerary.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="favorites")
    itinerary = db.relationship("Itinerary", back_populates="favorites")

    __table_args__ = (
        db.UniqueConstraint("user_id", "itinerary_id", name="uq_user_itinerary_favorite"),
    )


class ItineraryComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    itinerary_id = db.Column(db.Integer, db.ForeignKey("itinerary.id"), nullable=False)

    user = db.relationship("User", back_populates="comments")
    itinerary = db.relationship("Itinerary", back_populates="comments")
