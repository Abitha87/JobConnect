import os
from werkzeug.utils import secure_filename
from datetime import datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, abort
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)

from flask_wtf.csrf import CSRFProtect

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from functools import wraps

# ==========================================
# 1. FLASK APPLICATION CONFIGURATION
# ==========================================


app = Flask(__name__)

# Secret key
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "jobconnect-dev-secret-change-later"
)

# Persistent storage directory (configured on Render)
DATA_DIR = os.environ.get("JOBCONNECT_DATA_DIR")

if DATA_DIR:
    os.makedirs(DATA_DIR, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + os.path.join(DATA_DIR, "jobconnect.db")
    )
else:
    # Keep the existing local database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jobconnect.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Resume upload configuration
if DATA_DIR:
    UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
else:
    UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf"}


# ==========================================
# 2. INITIALIZE EXTENSIONS
# ==========================================

db = SQLAlchemy(app)

login_manager = LoginManager(app)

csrf = CSRFProtect(app)

login_manager.login_view = "login"


# ==========================================
# 3. USER DATABASE MODEL
# ==========================================

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False)


# ==========================================
# 4. JOB DATABASE MODEL
# ==========================================

class Job(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)

    company = db.Column(db.String(150), nullable=False)

    description = db.Column(db.Text, nullable=False)

    salary = db.Column(db.String(100), nullable=False)

    location = db.Column(db.String(100), nullable=False)

    category = db.Column(db.String(100), nullable=False)

    employer_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# ==========================================
# APPLICATION DATABASE MODEL
# ==========================================

class Application(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("job.id"),
        nullable=False
    )

    resume_filename = db.Column(
        db.String(255),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="Pending",
        nullable=False
    )

    applied_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    job = db.relationship("Job", backref="applications")
    user = db.relationship("User", backref="applications")
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "job_id",
            name="unique_job_application"
        ),
    )
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )
# ==========================================
# 5. LOAD LOGGED-IN USER
# ==========================================

@login_manager.user_loader
def load_user(user_id):

    return db.session.get(User, int(user_id))


# ==========================================
# 6. HOMEPAGE
# ==========================================

@app.route("/")
def home():

    return render_template("index.html")


# ==========================================
# 7. USER REGISTRATION
# ==========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:

        return redirect(url_for("home"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        email = request.form.get("email", "").strip().lower()

        password = request.form.get("password", "")

        role = request.form.get("role", "")

        if not name or not email or not password or role not in ["seeker", "employer"]:

            flash("Please fill all fields correctly.", "danger")

            return redirect(url_for("register"))

        if len(password) < 8:

            flash("Password must contain at least 8 characters.", "danger")

            return redirect(url_for("register"))

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:

            flash("Email already registered. Please log in.", "warning")

            return redirect(url_for("login"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role
        )

        db.session.add(new_user)

        db.session.commit()

        flash("Registration successful! Please log in.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


# ==========================================
# 8. USER LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:

        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            if user.role == "admin":
             return redirect(url_for("admin_dashboard"))

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


# ==========================================
# 9. USER DASHBOARD
# ==========================================

@app.route("/dashboard")
@login_required
def dashboard():

    return render_template("dashboard.html")


# ==========================================
# 10. EMPLOYER - POST A JOB
# ==========================================

@app.route("/post-job", methods=["GET", "POST"])
@login_required
def post_job():

    if current_user.role != "employer":

        abort(403)

    if request.method == "POST":

        title = request.form.get("title", "").strip()

        company = request.form.get("company", "").strip()

        description = request.form.get("description", "").strip()

        salary = request.form.get("salary", "").strip()

        location = request.form.get("location", "").strip()

        category = request.form.get("category", "").strip()

        if not all([
            title, company, description,
            salary, location, category
        ]):

            flash("Please fill in all fields.", "danger")

            return redirect(url_for("post_job"))

        new_job = Job(
            title=title,
            company=company,
            description=description,
            salary=salary,
            location=location,
            category=category,
            employer_id=current_user.id
        )

        db.session.add(new_job)

        db.session.commit()

        flash("Job posted successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("post_job.html")


# ==========================================
# 11. VIEW AND SEARCH JOBS
# ==========================================

@app.route("/jobs")
def jobs():

    keyword = request.args.get("keyword", "").strip()

    location = request.args.get("location", "").strip()

    category = request.args.get("category", "").strip()

    query = Job.query

    if keyword:

        query = query.filter(
            db.or_(
                Job.title.ilike(f"%{keyword}%"),
                Job.company.ilike(f"%{keyword}%"),
                Job.description.ilike(f"%{keyword}%")
            )
        )

    if location:

        query = query.filter(
            Job.location.ilike(f"%{location}%")
        )

    if category:

        query = query.filter(
            Job.category.ilike(f"%{category}%")
        )

    all_jobs = query.order_by(
        Job.created_at.desc()
    ).all()

    return render_template(
        "jobs.html",
        jobs=all_jobs,
        keyword=keyword,
        location=location,
        category=category
    )


# ==========================================
# 12. EMPLOYER - VIEW OWN JOB LISTINGS
# ==========================================

@app.route("/my-jobs")
@login_required
def my_jobs():

    if current_user.role != "employer":

        abort(403)

    employer_jobs = Job.query.filter_by(
        employer_id=current_user.id
    ).order_by(
        Job.created_at.desc()
    ).all()

    return render_template(
        "my_jobs.html",
        jobs=employer_jobs
    )
# Admin Dashboard
@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        abort(403)

    total_users = User.query.count()
    total_seekers = User.query.filter_by(role="seeker").count()
    total_employers = User.query.filter_by(role="employer").count()
    total_jobs = Job.query.count()

    users = User.query.order_by(User.id.desc()).all()
    jobs = Job.query.order_by(Job.created_at.desc()).all()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_seekers=total_seekers,
        total_employers=total_employers,
        total_jobs=total_jobs,
        users=users,
        jobs=jobs
    )


# Admin: Delete a job
@app.route("/admin/delete-job/<int:job_id>", methods=["POST"])
@login_required
def admin_delete_job(job_id):
    if current_user.role != "admin":
        abort(403)

    job = Job.query.get_or_404(job_id)

    # Delete applications linked to this job first
    Application.query.filter_by(job_id=job.id).delete()

    db.session.delete(job)
    db.session.commit()

    flash("Job deleted successfully.", "success")
    return redirect(url_for("admin_dashboard"))


# Admin: Delete a user
@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@login_required
def admin_delete_user(user_id):
    if current_user.role != "admin":
        abort(403)

    user = User.query.get_or_404(user_id)

    # Prevent the admin from deleting their own account
    if user.id == current_user.id:
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for("admin_dashboard"))

    # Delete applications submitted by this user
    Application.query.filter_by(user_id=user.id).delete()

    # Delete jobs posted by this user and their applications
    user_jobs = Job.query.filter_by(employer_id=user.id).all()

    for job in user_jobs:
        Application.query.filter_by(job_id=job.id).delete()
        db.session.delete(job)

    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully.", "success")
    return redirect(url_for("admin_dashboard"))

# ==========================================
# JOB SEEKER - APPLY FOR A JOB
# ==========================================

@app.route("/apply/<int:job_id>", methods=["POST"])
@login_required
def apply_job(job_id):

    if current_user.role != "seeker":
        abort(403)

    job = db.session.get(Job, job_id)

    if job is None:
        abort(404)

    existing_application = Application.query.filter_by(
        user_id=current_user.id,
        job_id=job_id
    ).first()

    if existing_application:
        flash("You have already applied for this job.", "warning")
        return redirect(url_for("jobs"))

    resume = request.files.get("resume")

    if not resume or not resume.filename:
        flash("Please upload your resume.", "danger")
        return redirect(url_for("jobs"))

    if not allowed_file(resume.filename):
        flash("Only PDF resumes are allowed.", "danger")
        return redirect(url_for("jobs"))

    # Check actual PDF file signature
    file_start = resume.stream.read(5)
    resume.stream.seek(0)

    if file_start != b"%PDF-":
        flash("The uploaded file is not a valid PDF.", "danger")
        return redirect(url_for("jobs"))

    safe_name = secure_filename(resume.filename)

    if not safe_name:
        flash("Invalid resume filename.", "danger")
        return redirect(url_for("jobs"))

    # Generate a unique filename
    unique_filename = (
        f"user_{current_user.id}_job_{job_id}_"
        f"{os.urandom(8).hex()}.pdf"
    )

    resume.save(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            unique_filename
        )
    )

    application = Application(
        user_id=current_user.id,
        job_id=job_id,
        resume_filename=unique_filename
    )

    db.session.add(application)
    db.session.commit()

    flash("Your job application was submitted successfully!", "success")

    return redirect(url_for("my_applications"))


# ==========================================
# JOB SEEKER - VIEW MY APPLICATIONS
# ==========================================

@app.route("/my-applications")
@login_required
def my_applications():

    if current_user.role != "seeker":
        abort(403)

    applications = Application.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Application.applied_at.desc()
    ).all()

    return render_template(
        "my_applications.html",
        applications=applications
    )


# ==========================================
# EMPLOYER - VIEW APPLICATIONS
# ==========================================

@app.route("/applications/<int:job_id>")
@login_required
def view_applications(job_id):

    if current_user.role != "employer":
        abort(403)

    job = db.session.get(Job, job_id)

    if job is None:
        abort(404)

    # Employers can only view applications for their own jobs
    if job.employer_id != current_user.id:
        abort(403)

    applications = Application.query.filter_by(
        job_id=job_id
    ).order_by(
        Application.applied_at.desc()
    ).all()

    return render_template(
        "applications.html",
        applications=applications,
        job=job
    )


# ==========================================
# EMPLOYER - UPDATE APPLICATION STATUS
# ==========================================

@app.route(
    "/update-application/<int:application_id>",
    methods=["POST"]
)
@login_required
def update_application(application_id):

    if current_user.role != "employer":
        abort(403)

    application = db.session.get(Application, application_id)

    if application is None:
        abort(404)

    job = db.session.get(Job, application.job_id)

    if job is None or job.employer_id != current_user.id:
        abort(403)

    new_status = request.form.get("status", "")

    if new_status not in ["Pending", "Accepted", "Rejected"]:
        abort(400)

    application.status = new_status

    db.session.commit()

    flash("Application status updated successfully.", "success")

    return redirect(
        url_for("view_applications", job_id=job.id)
    )


# ==========================================
# EMPLOYER - DOWNLOAD RESUME
# ==========================================

@app.route("/download-resume/<int:application_id>")
@login_required
def download_resume(application_id):

    if current_user.role != "employer":
        abort(403)

    application = db.session.get(Application, application_id)

    if application is None:
        abort(404)

    job = db.session.get(Job, application.job_id)

    if job is None or job.employer_id != current_user.id:
        abort(403)

    from flask import send_from_directory

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        application.resume_filename,
        as_attachment=True,
        download_name="resume.pdf"
    )

# ==========================================
# 13. USER LOGOUT
# ==========================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("You have logged out successfully.", "info")

    return redirect(url_for("home"))


# ==========================================
# 14. CREATE DATABASE TABLES
# ==========================================

with app.app_context():

    db.create_all()


# ==========================================
# 15. RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)
