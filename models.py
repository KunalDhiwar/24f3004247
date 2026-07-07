from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum

db=SQLAlchemy()

class Users(db.Model):
      __tablename__ = "user"

      role = db.Column(Enum("Admin", "Trek Staff", "Trekker", name="role"))
      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.Unicode(50), nullable=False)
      email = db.Column(db.Unicode(50), unique=True)
      password = db.Column(db.Unicode(50), nullable=False)

      booking = db.relationship("Booking", back_populates="user", cascade="all, delete-orphan", lazy=True)

class Staff_Profile(db.Model):
      __tablename__ = "staff_profile"

      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.Unicode(50), nullable=False)
      email = db.Column(db.Unicode(50), unique=True)
      trek_id = db.Column(db.Integer, db.ForeignKey("trek.id"))
      status = db.Column(Enum("Approved", "Pending", name="approve_status"))

      trek = db.relationship("Trek", back_populates="staff")

class Trek(db.Model):
      __tablename__ = "trek"

      id = db.Column(db.Integer, primary_key=True)
      name = db.Column(db.Unicode(50), nullable=False)
      location = db.Column(db.Unicode(50), nullable=False)
      dificulty = db.Column(Enum("Easy", "Medium", "Hard", name="dificulty_level"))
      available_slot = db.Column(db.Integer, nullable=False)
      total_slot = db.Column(db.Integer, nullable=False)
      assigned_staff_id = db.Column(db.Integer, db.ForeignKey("staff_profile.id"))
      status = db.Column(Enum("Pending", "Approved","Open", "Closed", "Completed", name="status"))
      start_date = db.Column(db.Date)
      end_date = db.Column(db.Date)
      price = db.Column(db.Float)

      booking = db.relationship("Booking", back_populates="trek", cascade="all, delete-orphan", lazy=True)
      staff = db.relationship("Staff_Profile", back_populates="trek", lazy=True)

class Booking(db.Model):
      __tablename__ = "booking"

      id = db.Column(db.Integer, primary_key=True)
      user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
      trek_id = db.Column(db.Integer, db.ForeignKey("trek.id"))
      booking_date = db.Column(db.Date, nullable = False)
      status = db.Column(Enum("Booked", "Cancelled", "Completed", name="booking_status"))
      payment = db.Column(Enum("Pending", "Completed", name="payment_status"))

      user = db.relationship("Users", back_populates="booking")
      trek = db.relationship("Trek", back_populates="booking")


def default_user():
    if Users.query.count==0:
          user1 = Users(
                role = "Admin",
                id = 1001,
                name = "Aman",
                email = "example1.@emai.com",
                password = "A1001"
          )

          user2 = Users(
                role = "Admin",
                id = 1002,
                name = "Rahul",
                email = "example2.@emai.com",
                password = "A1002"
          )

          db.session.add(user1)
          db.session.add(user2)
          db.session.commit()
