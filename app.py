from flask import Flask, render_template, request, flash, redirect, url_for, session
from models import db, default_user
from models import Trek, Users, Booking, Staff_Profile
#from decoraters import login_required, role_required
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Home 
@app.route("/")
def home():
    return render_template("home.html", treks=[], search="")

@app.route("/search")
def search():
    search_text = request.args.get("query", "").strip()

    if search_text == "":
        return render_template("home.html", treks=[], search="")
    
    # Search
    treks = Trek.query.filter(
        (Trek.location.ilike(f"%{search_text}%")) |
        (Trek.name.ilike(f"%{search_text}%"))
    ).all()

    return render_template("home.html", treks=treks, search=search_text)


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form["role"]

        # Check password match
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        # Check existing email

        existing_user = Users.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        # Create User
        new_user = Users(
            name=name,
            email=email,
            password=password,
            role=role
            )
        db.session.add(new_user)
        db.session.commit()

        # If Staff create Staff_Profile
        if role == "Trek Staff":
            staff_profile = Staff_Profile(
                user_id=new_user.id,
                status="Pending"
            )
            db.session.add(staff_profile)

            db.session.commit()

            flash("Registration successful. Wait for admin approval.", "success")

        else:
            flash(
                "Registration successful. You can login now.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        email = request.form["email"].strip()
        password = request.form["password"]

        # Find user
        user = Users.query.filter_by(
            email=email,
            password=password,
            role=role
        ).first()

        if not user:
            flash("Invalid email or password")
            return redirect(url_for("login"))
        
        
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["role"] = user.role

        # Admin
        if user.role == "Admin":
            flash(f"Welcome {user.name} !", "success")
            return redirect(url_for("admin_dashboard"))
        
        # Staff
        elif user.role == "Trek Staff":
            staff = user.staff_profile

            if staff is None:
                flash("Staff profile not found.", "danger")
                return redirect(url_for("login"))
            if staff.status != "Approved":
                flash("Your account is waiting for Admin approval", "warning")
                return redirect(url_for("login"))
            else:
                flash(f"Welcome {user.name} !", "success")
                return redirect(url_for("staff_dashboard"))
        
        # Trekker    
        elif user.role == "Trekker":
            flash(f"Welcome {user.name} !", "success")
            return redirect(url_for("trekker_dashboard"))
        
    return render_template("login.html")


@app.route("/logout")
#@login_required
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/admin_dashboard")
#@role_required("Admin")
def admin_dashboard():

    section = request.args.get("section", "dashboard")
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)

    per_page = 10
    data = None

    if section == "users":
        query = Users.query.filter_by(role="Trekker")

        if search:
            query = query.filter(
                (Users.name.ilike(f"%{search}%")) |
                (Users.id.cast(db.String).ilike(f"%{search}%"))
                )

        data = query.paginate(page=page, per_page=per_page, error_out=False)

    elif section == "staff":
        query = Users.query.filter_by(role="Trek Staff")

        if search:
            query = query.filter(
                (Users.name.ilike(f"%{search}%")) |
                (Users.id.cast(db.String).ilike(f"%{search}%"))
            )

        data = query.paginate(page=page, per_page=per_page, error_out=False)

    elif section == "treks":
        query = Trek.query

        if search:
            query = query.filter(
                (Trek.name.ilike(f"%{search}%")) |
                (Trek.location.ilike(f"%{search}%"))
            )

        data = query.paginate(page=page, per_page=per_page, error_out=False)

    elif section == "bookings":
        query = Booking.query
        data = query.paginate(page=page, per_page=per_page, error_out=False)

    elif section == "pending":
        query = Staff_Profile.query.filter_by(status="Pending")
        data = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "admin_dashboard.html",
        section=section,
        data=data,
        search=search,
        total_users=Users.query.filter_by(role="Trekker").count(),
        total_staff=Users.query.filter_by(role="Trek Staff").count(),
        total_treks=Trek.query.count(),
        total_bookings=Booking.query.count(),
        pending_staff=Staff_Profile.query.filter_by(status="Pending").count()
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        default_user()
    app.run(debug=True)

