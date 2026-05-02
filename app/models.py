from app.extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    itineraries = db.relationship("Itinerary", back_populates="user")

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

    days = db.relationship(
        "ItineraryDay",
        back_populates="itinerary",
        cascade="all, delete-orphan"
    )


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
