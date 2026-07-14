from flask import Flask, render_template, request, flash, redirect, url_for, session
from models import db, default_user
from models import Trek, Users, Booking, Staff_Profile
from decoraters import login_required, role_required
from dotenv import load_dotenv
import os
from datetime import datetime

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
        
        if user.status == 'Deactivated':
            flash('Your account has been deactivated. Please contact the admin.', 'danger')
            return redirect(url_for('login'))
        
        
        session["user_id"] = user.id
        session["user_name"] = user.name
        session["role"] = user.role
        session["user_email"] = user.email

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
@login_required
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/admin_dashboard")
@role_required(("Admin"))
def admin_dashboard():

    section = request.args.get("section", "pending")
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

@app.route("/create_trek", methods=["GET", "POST"])
@role_required("Admin")
def create_trek():
    if request.method == "POST":
        name = request.form["name"].strip()
        location = request.form["location"].strip()
        difficulty = request.form["difficulty"]
        total_slot = request.form["total_slot"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        price = request.form["price"]

        # -----------------------------
        # Validation
        # -----------------------------
        if not name:
            flash("Trek name is required.", "danger")
            return redirect(url_for("create_trek"))

        if not location:
            flash("Location is required.", "danger")
            return redirect(url_for("create_trek"))

        try:
            total_slot = int(total_slot)

            if total_slot <= 0:
                flash("Total slots must be greater than 0.", "danger")
                return redirect(url_for("create_trek"))

        except ValueError:
            flash("Invalid total slots.", "danger")
            return redirect(url_for("create_trek"))

        try:
            price = int(price)

            if price < 0:
                flash("Price cannot be negative.", "danger")
                return redirect(url_for("create_trek"))

        except ValueError:
            flash("Invalid price.", "danger")
            return redirect(url_for("create_trek"))
        
        existing_trek = Trek.query.filter_by(
            name=name,
            location=location
        ).first()

        if existing_trek:
            flash(
                "This trek already exists.",
                "danger"
            )
            return redirect(url_for("create_trek"))

        try:
            start_date = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()

            end_date = datetime.strptime(
                end_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            flash("Invalid date.", "danger")
            return redirect(url_for("create_trek"))

        if end_date < start_date:
            flash(
                "End date cannot be before start date.",
                "danger"
            )

            return redirect(url_for("create_trek"))

        # -----------------------------
        # Create Trek
        # -----------------------------
        trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            total_slot=total_slot,
            available_slot=total_slot,
            status="Pending",
            start_date=start_date,
            end_date=end_date,
            price=price
        )
        db.session.add(trek)
        db.session.commit()

        flash(
            "Trek created successfully.",
            "success"
        )

        return redirect(
            url_for(
                "admin_dashboard",
                section="treks"
            )
        )

    return render_template("trek_create.html")


@app.route("/edit_trek/<int:trek_id>", methods=["GET", "POST"])
@role_required("Admin")
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    if request.method == "POST":
        name = request.form["name"].strip()
        location = request.form["location"].strip()
        difficulty = request.form["difficulty"]
        total_slot = request.form["total_slot"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        price = request.form["price"]
        status = request.form["status"] if "status" in request.form else trek.status

        # -----------------------------
        # Validation
        # -----------------------------
        if not name:
            flash(
                "Trek name is required.",
                "danger"
            )
            return redirect(url_for("edit_trek", trek_id=trek.id))
        
        if not location:
            flash(
                "Location is required.",
                "danger"
            )
            return redirect(
                url_for(
                    "edit_trek",
                    trek_id=trek.id
                )
            )
        try:
            total_slot = int(total_slot)
            if total_slot <= 0:
                flash(
                    "Total slots must be greater than zero.",
                    "danger"
                )
                return redirect(
                    url_for(
                        "edit_trek",
                        trek_id=trek.id
                    )
                )

        except ValueError:
            flash(
                "Invalid total slots.",
                "danger"
            )
            return redirect(
                url_for(
                    "edit_trek",
                    trek_id=trek.id
                )
            )

        try:
            price = int(price)
            if price < 0:
                flash(
                    "Price cannot be negative.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "edit_trek",
                        trek_id=trek.id
                    )
                )

        except ValueError:
            flash(
                "Invalid price.",
                "danger"
            )
            return redirect(
                url_for(
                    "edit_trek",
                    trek_id=trek.id
                )
            )

        # -----------------------------
        # Duplicate Check
        # -----------------------------
        existing = Trek.query.filter(
            Trek.name == name,
            Trek.location == location,
            Trek.id != trek.id
        ).first()

        if existing:
            flash(
                "Another trek with the same name and location already exists.",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_trek",
                    trek_id=trek.id
                )
            )

        # -----------------------------
        # Date Validation
        # -----------------------------

        try:
            start_date = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()

            end_date = datetime.strptime(
                end_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            flash(
                "Invalid date.",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_trek",
                    trek_id=trek.id
                )
            )

        if end_date < start_date:
            flash(
                "End date cannot be before start date.",
                "danger"
            )

            return redirect(
                url_for(
                    "edit_trek",
                    trek_id=trek.id
                )
            )

        # -----------------------------
        # Update Trek
        # -----------------------------
        trek.name = name
        trek.location = location
        trek.difficulty = difficulty
        trek.total_slot = total_slot
        trek.start_date = start_date
        trek.end_date = end_date
        trek.price = price
        trek.status = status

        db.session.commit()

        flash(
            "Trek updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "admin_dashboard",
                section="treks"
            )
        )
    return render_template(
        "trek_create.html",
        trek=trek
    )

@app.route("/delete_trek/<int:trek_id>")
@role_required("Admin")
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    # Remove assigned staff
    for staff in trek.staff:
        staff.trek_id = None

    # Delete trek
    db.session.delete(trek)
    db.session.commit()

    flash(
        "Trek deleted successfully.",
        "success"
    )
    return redirect(
        url_for(
            "admin_dashboard",
            section="treks"
        )
    )


@app.route('/trek_info/<int:trek_id>')
@role_required("Admin", "Trek Staff", "Trekker")
def trek_info(trek_id):

    # Get Trek
    trek = Trek.query.get_or_404(trek_id)



    # Render Page
    return render_template(
        'trek_info.html',
        trek=trek
    )


@app.route('/deactivate_trekker/<int:user_id>')
@role_required("Admin")
def deactivate_trekker(user_id):

    # Find User
    user = Users.query.get(user_id)

    if not user:
        flash('Trekker not found.', 'danger')
        return redirect(url_for('admin_dashboard', section='users'))

    # Role Validation
    if user.role != 'Trekker':
        flash('Invalid user selected.', 'warning')
        return redirect(url_for('admin_dashboard', section='users'))

    # Already Deactivated
    if user.status == 'Deactivated':
        flash('Trekker is already deactivated.', 'info')
        return redirect(url_for('admin_dashboard', section='users'))

    # Deactivate Account
    user.status = 'Deactivated'

    db.session.commit()

    flash('Trekker deactivated successfully.', 'success')

    return redirect(url_for('admin_dashboard', section='users'))


@app.route('/approve_staff/<int:staff_id>')
@role_required("Admin")
def approve_staff(staff_id):

    staff = Staff_Profile.query.get(staff_id)

    if not staff:
        flash("Staff record not found.", "danger")
        return redirect(url_for('admin_dashboard', section='pending'))

    if staff.status == "Approved":
        flash("Staff is already approved.", "info")
        return redirect(url_for('admin_dashboard', section='pending'))

    if staff.status == "Blacklisted":
        flash("Blacklisted staff cannot be approved.", "warning")
        return redirect(url_for('admin_dashboard', section='pending'))

    staff.status = "Approved"

    db.session.commit()

    flash("Staff approved successfully.", "success")

    return redirect(url_for('admin_dashboard', section='pending'))


@app.route('/reject_staff/<int:staff_id>')
@role_required("Admin")
def reject_staff(staff_id):

    staff = Staff_Profile.query.get(staff_id)

    if not staff:
        flash("Staff record not found.", "danger")
        return redirect(url_for('admin_dashboard', section='pending'))

    user = staff.user

    # Delete Staff Profile
    db.session.delete(staff)

    # Delete User Account
    if user:
        db.session.delete(user)

    db.session.commit()

    flash("Staff registration rejected successfully.", "success")

    return redirect(url_for('admin_dashboard', section='pending'))


@app.route('/assign_staff/<int:staff_id>', methods=['GET', 'POST'])
@role_required("Admin")
def assign_staff(staff_id):

    staff = Staff_Profile.query.get(staff_id)

    if not staff:
        flash("Staff record not found.", "danger")
        return redirect(url_for('admin_dashboard', section='staff'))


    # Only Approved Staff can be assigned

    if staff.status != "Approved":
        flash("Only approved staff can be assigned.", "warning")
        return redirect(url_for('admin_dashboard', section='staff'))


    # GET Request

    if request.method == "GET":

        treks = Trek.query.filter(
                Trek.status.in_(["Approved", "Open"])
            ).all()

        return render_template(
            "assign_staff.html",
            staff=staff,
            treks=treks
        )


    # POST Request

    trek_id = request.form.get('trek_id')


    if not trek_id:
        flash("Please select a trek.", "danger")
        return redirect(request.url)


    trek = Trek.query.get(trek_id)


    if not trek:
        flash("Trek not found.", "danger")
        return redirect(request.url)


    staff.trek_id = trek.id

    db.session.commit()


    flash("Staff assigned successfully.", "success")

    return redirect(
        url_for('admin_dashboard', section='staff')
    )


@app.route('/blacklist_staff/<int:staff_id>')
@role_required("Admin")
def blacklist_staff(staff_id):

    staff = Staff_Profile.query.get(staff_id)

    if not staff:
        flash("Staff record not found.", "danger")
        return redirect(url_for('admin_dashboard', section='staff'))


    if staff.status == "Blacklisted":

        flash("Staff is already blacklisted.", "info")
        return redirect(url_for('admin_dashboard', section='staff'))


    # Remove assigned trek
    staff.trek_id = None


    # Update staff status
    staff.status = "Blacklisted"


    db.session.commit()


    flash("Staff blacklisted and trek assignment removed successfully.", "success")


    return redirect(
        url_for('admin_dashboard', section='staff')
    )


@app.route('/staff_dashboard', methods=["GET", "POST"])
@role_required("Trek Staff")
def staff_dashboard():

    section = request.args.get("section","trek")

    # Get Logged-in User
    user = Users.query.get(session.get("user_id"))
    

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("login"))


    # Get Staff Profile
    staff = user.staff_profile

    if not staff:
        flash("Staff profile not found.", "danger")
        return redirect(url_for("login"))


    # Access Control
    if staff.status != "Approved":
        flash("You are not authorized to access this dashboard.", "warning")
        return redirect(url_for("login"))


    # Assigned Trek
    trek = staff.trek


    # =========================
    # Status Update
    # =========================

    if request.method == "POST":

        if not trek:
            flash(
                "No trek assigned to update.",
                "warning"
            )
            return redirect(url_for("staff_dashboard"))


        new_status = request.form.get("status")


        # Valid Status Flow

        allowed_status = {

            "Approved": "Open",

            "Open": "Closed",

            "Closed": "Completed"

        }


        if trek.status == "Completed":
            flash(
                "Completed trek status cannot be changed.",
                "warning"
            )
            for booking in trek.booking:

                if booking.status == "Booked":

                    booking.status = "Completed"

                    booking.payment = "Completed"

        elif new_status != allowed_status.get(trek.status):

            flash(
                "Invalid status update.",
                "danger"
            )

        else:

            trek.status = new_status

            db.session.commit()

            flash(
                "Trek status updated successfully.",
                "success"
            )


        return redirect(
            url_for("staff_dashboard")
        )


    # =========================
    # Dashboard Cards
    # =========================

    assigned_trek = 0
    total_participants = 0


    # Participant Pagination

    page = request.args.get(
        "page",
        1,
        type=int
    )

    per_page = 10


    participants = None


    if trek:

        assigned_trek = 1


        participants = Booking.query.filter_by(
            trek_id=trek.id
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )


        total_participants = Booking.query.filter_by(
            trek_id=trek.id
        ).count()


    return render_template(
        "staff_dashboard.html",

        staff=staff,

        trek=trek,

        assigned_trek=assigned_trek,

        total_participants=total_participants,

        participants=participants,
        section=section
        
    )


@app.route('/trekker_dashboard')
@role_required("Trekker")
def trekker_dashboard():

    # Logged-in user
    user_id = session.get("user_id")

    if not user_id:
        flash(
            "Please login first.",
            "warning"
        )
        return redirect(url_for("login"))


    user = Users.query.get(user_id)


    if not user:
        flash(
            "User not found.",
            "danger"
        )
        return redirect(url_for("login"))


    if user.role != "Trekker":

        flash(
            "Access denied.",
            "danger"
        )

        return redirect(url_for("login"))



    # =========================
    # Section Handling
    # =========================

    section = request.args.get(
        "section",
        "treks"
    )


    search = request.args.get(
        "search",
        ""
    ).strip()



    page = request.args.get(
        "page",
        1,
        type=int
    )


    per_page = 10



    data = None



    # =========================
    # AVAILABLE TREKS
    # =========================

    if section == "treks":


        query = Trek.query.filter_by(
            status="Open"
        )



        if search:


            query = query.filter(

                (Trek.name.ilike(
                    f"%{search}%"
                ))

                |

                (Trek.location.ilike(
                    f"%{search}%"
                ))

            )



        data = query.paginate(

            page=page,

            per_page=per_page,

            error_out=False

        )




    # =========================
    # MY BOOKINGS
    # =========================


    elif section == "bookings":


        query = Booking.query.filter_by(

            user_id=user.id,

            status="Booked"

        )


        data = query.paginate(

            page=page,

            per_page=per_page,

            error_out=False

        )




    # =========================
    # HISTORY
    # =========================


    elif section == "history":


        query = Booking.query.filter_by(

            user_id=user.id

        )



        data = query.paginate(

            page=page,

            per_page=per_page,

            error_out=False

        )




    return render_template(

        "trekker_dashboard.html",

        section=section,

        data=data,

        search=search,


        available_treks=Trek.query.filter_by(
            status="Open"
        ).count(),


        my_bookings=Booking.query.filter_by(

            user_id=user.id,

            status="Booked"

        ).count(),


        history_count=Booking.query.filter_by(

            user_id=user.id

        ).count()

    )


@app.route('/book_trek/<int:trek_id>')
@role_required("Trekker")
def book_trek(trek_id):

    user_id = session.get("user_id")

    user = Users.query.get(user_id)

    if not user:

        flash(
            "User not found.",
            "danger"
        )

        return redirect(
            url_for("login")
        )



    # =========================
    # Role Check
    # =========================

    if user.role != "Trekker":

        flash(
            "Only trekkers can book treks.",
            "danger"
        )

        return redirect(
            url_for("trekker_dashboard")
        )




    # =========================
    # Trek Check
    # =========================

    trek = Trek.query.get(trek_id)



    if not trek:

        flash(
            "Trek not found.",
            "danger"
        )

        return redirect(
            url_for("trekker_dashboard")
        )




    # =========================
    # Status Check
    # =========================

    if trek.status != "Open":

        flash(
            "This trek is not available for booking.",
            "warning"
        )

        return redirect(
            url_for(
                "trekker_dashboard",
                section="treks"
            )
        )




    # =========================
    # Slot Check
    # =========================

    if trek.available_slot <= 0:


        flash(
            "Sorry, this trek is full.",
            "warning"
        )


        return redirect(
            url_for(
                "trekker_dashboard",
                section="treks"
            )
        )





    # =========================
    # Duplicate Booking Check
    # =========================


    existing_booking = Booking.query.filter_by(

        user_id=user.id,

        trek_id=trek.id,

        status="Booked"

    ).first()



    if existing_booking:


        flash(
            "You have already booked this trek.",
            "info"
        )


        return redirect(
            url_for(
                "trekker_dashboard",
                section="treks"
            )
        )






    # =========================
    # Create Booking
    # =========================


    booking = Booking(

        user_id=user.id,

        trek_id=trek.id,

        booking_date=datetime.today().date(),

        status="Booked",

        payment="Pending"

    )


    db.session.add(booking)



    # Reduce Available Slot

    trek.available_slot -= 1



    db.session.commit()



    flash(
        "Trek booked successfully.",
        "success"
    )



    return redirect(

        url_for(
            "trekker_dashboard",
            section="bookings"
        )

    )


@app.route('/cancel_booking/<int:booking_id>')
@role_required("Trekker")
def cancel_booking(booking_id):

    user_id = session.get("user_id")

    user = Users.query.get(user_id)

    if not user or user.role != "Trekker":
        flash("Unauthorized access.", "danger")
        return redirect(url_for("login"))

    # =========================
    # Booking Check
    # =========================

    booking = Booking.query.get(booking_id)

    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for("trekker_dashboard", section="bookings"))

    # =========================
    # Ownership Check
    # =========================

    if booking.user_id != user.id:
        flash("You are not allowed to cancel this booking.", "danger")
        return redirect(url_for("trekker_dashboard", section="bookings"))

    # =========================
    # Status Check
    # =========================

    if booking.status != "Booked":
        flash("Only booked treks can be cancelled.", "warning")
        return redirect(url_for("trekker_dashboard", section="bookings"))

    # =========================
    # Update Booking Status
    # =========================

    booking.status = "Cancelled"

    # =========================
    # Restore Slot
    # =========================

    if booking.trek:

        if booking.trek.available_slot < booking.trek.total_slot:
            booking.trek.available_slot += 1

    db.session.commit()

    flash("Booking cancelled successfully.", "success")

    return redirect(url_for("trekker_dashboard", section="bookings"))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        default_user()
    app.run(debug=True)

