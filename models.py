from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum

db=SQLAlchemy()

class Users(db.Model):
      __tablename__ = "user"

      role = db.Column(Enum("Admin", "Trek Staff", "Trekker", name="role"), default="Trekker")
      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.Unicode(50), nullable=False)
      email = db.Column(db.Unicode(50), unique=True, nullable=False)
      password = db.Column(db.Unicode(50), nullable=False)

      staff_profile = db.relationship("Staff_Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
      booking = db.relationship("Booking", back_populates="user", cascade="all, delete-orphan", lazy=True)

class Staff_Profile(db.Model):
      __tablename__ = "staff_profile"

      id = db.Column(db.Integer, primary_key=True)
      user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
      trek_id = db.Column(db.Integer, db.ForeignKey("trek.id"))
      status = db.Column(Enum("Approved", "Pending", name="approve_status"), default="Pending")

      user = db.relationship("Users", back_populates="staff_profile")
      trek = db.relationship("Trek", back_populates="staff")

class Trek(db.Model):
      __tablename__ = "trek"

      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.Unicode(50), nullable=False)
      location = db.Column(db.Unicode(50), nullable=False)
      difficulty = db.Column(Enum("Easy", "Medium", "Hard", name="dificulty_level"), default="Easy")
      available_slot = db.Column(db.Integer, nullable=False)
      total_slot = db.Column(db.Integer, nullable=False)
      status = db.Column(Enum("Pending", "Approved","Open", "Closed", "Completed", name="status"), default="Pending")
      start_date = db.Column(db.Date)
      end_date = db.Column(db.Date)
      price = db.Column(db.Integer)

      booking = db.relationship("Booking", back_populates="trek", cascade="all, delete-orphan", lazy=True)
      staff = db.relationship("Staff_Profile", back_populates="trek", lazy=True)

class Booking(db.Model):
      __tablename__ = "booking"

      id = db.Column(db.Integer, primary_key=True)
      user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
      trek_id = db.Column(db.Integer, db.ForeignKey("trek.id"))
      booking_date = db.Column(db.Date, nullable = False)
      status = db.Column(Enum("Booked", "Cancelled", "Completed", name="booking_status"), default="Booked")
      payment = db.Column(Enum("Pending", "Completed", name="payment_status"), default="Pending")

      user = db.relationship("Users", back_populates="booking")
      trek = db.relationship("Trek", back_populates="booking")


def default_user():
    if Users.query.first() is None:

        user1 = Users(
            role="Admin",
            name="Aman",
            email="example1@email.com",
            password="A1001"
        )

        user2 = Users(
            role="Admin",
            name="Rahul",
            email="example2@email.com",
            password="A1002"
        )

        db.session.add_all([user1, user2])
        db.session.commit()
