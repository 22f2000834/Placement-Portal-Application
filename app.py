from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from datetime import datetime
from flask import redirect, render_template, request, url_for, session, flash
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.secret_key = os.environ.get("SECRET_KEY", "secretkeyforproject")
app.config['UPLOAD_FOLDER'] = 'static/resumes'


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_blacklisted = db.Column(db.Boolean, default=False)

    # One-to-one relationships between company and user
    company_profile = db.relationship(
        "Company",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    #relationship between user and student
    student_profile = db.relationship(
        "Student",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Company(db.Model):
    __tablename__ = "company"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(150), unique=True, nullable=False)
    company_description = db.Column(db.String(200), nullable=False)
    company_website = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=False, default="Pending")

    # FK reference TABLE name "users"
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True
    )

    user = db.relationship("User", back_populates="company_profile")

    #relationship between drive and company
    drives = db.relationship(
        "Placement_Drive",
        back_populates="company",
        cascade="all, delete-orphan"
    )


class Placement_Drive(db.Model):
    __tablename__ = "placement_drive"

    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    status = db.Column(db.String(50), nullable=False, default="Pending")
    verified = db.Column(db.String(50), nullable = False, default="In Review")
    job_title = db.Column(db.String(50), nullable=False)
    job_description = db.Column(db.String(500), nullable=False)
    eligibility_criteria = db.Column(db.String(500), nullable=False)
    application_deadline = db.Column(db.DateTime, nullable=False)

    # FK to company table
    company_id = db.Column(
        db.Integer, db.ForeignKey("company.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    #relationship between company and drive
    company = db.relationship("Company", back_populates="drives")

    applications = db.relationship(
        "Application",
        back_populates="drive",
        cascade="all, delete-orphan"
    )


class Student(db.Model):
    __tablename__ = "student"

    id = db.Column(db.Integer, primary_key=True)
    student_iid = db.Column(db.String(30), unique=True, nullable=False)
    f_name = db.Column(db.String(50), nullable=False)
    l_name = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(150), nullable=False)
    cgpa = db.Column(db.Float, nullable=False)
    batch_year = db.Column(db.Integer, nullable=False)
    placed = db.Column(db.Boolean, default=False, nullable=False)
    resume = db.Column(db.String(200), nullable=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True
    )

    user = db.relationship("User", back_populates="student_profile")

    applications = db.relationship(
        "Application",
        back_populates="student",
        cascade="all, delete-orphan"
    )


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)

    # FK strings must match your actual table names
    student_id = db.Column(
        db.Integer, db.ForeignKey("student.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    drive_id = db.Column(
        db.Integer, db.ForeignKey("placement_drive.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    applied_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default="applied", nullable=False, index=True)

    student = db.relationship("Student", back_populates="applications")
    drive = db.relationship("Placement_Drive", back_populates="applications")

    __table_args__ = (
        db.UniqueConstraint("student_id", "drive_id", name="uq_student_drive"),
    )



@app.route('/')
def initial_page():
    session.pop('name', None)
    session.pop('id', None)
    session.pop('role', None)
    return render_template("base.html")

# -------------- COMPANY REGISTRATION ---------------------- #

@app.route('/companyreg', methods = ["POST", "GET"])
def companyReg():
    if request.method == "POST":
        name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(username = name, email = email).first()
        if user:
            flash("User already exists. Please login.", "error")
            return render_template("companyreg.html")

        new_user = User(username = name, email = email, password = password, role = "Company")
        db.session.add(new_user)
        db.session.commit()

        session["pending_company_user_id"] = new_user.id

        flash("Account created! Now add your company details.", "success")
        return redirect(url_for("comp_details"))

    return render_template("companyreg.html")

@app.route('/companyreg/details', methods=["POST", "GET"])
def comp_details():
    
    user_id = session.get("pending_company_user_id")

    if not user_id:
        flash("Please create your company account first.", "error")
        return redirect(url_for("companyReg"))

    user = User.query.get(user_id)
    if not user or user.role != "Company":
        flash("Invalid registration session. Please register again.", "error")
        session.pop("pending_company_user_id", None)
        return redirect(url_for("companyReg"))

    if user.company_profile:
        flash("Company profile already exists. Please login.", "error")
        session.pop("pending_company_user_id", None)
        return redirect(url_for("login"))

    if request.method == "POST":
        company_name = request.form.get("company_name")
        company_description = request.form.get("company_description")
        company_website = request.form.get("company_website")

        if not company_name or not company_description or not company_website:
            flash("Please fill all company fields.", "error")
            return render_template("company_details.html")

        existing_company = Company.query.filter_by(company_name=company_name).first()
        if existing_company:
            flash("Company name already registered. Try another name.", "error")
            return render_template("company_details.html")

        new_company = Company(
            company_name=company_name,
            company_description=company_description,
            company_website=company_website,
            user_id=user.id
        )

        db.session.add(new_company)
        db.session.commit()

        session.pop("pending_company_user_id", None)

        flash("Company registered successfully! Please login now.", "success")
        return redirect(url_for("login"))

    return render_template("company_details.html")

@app.route('/studentreg', methods = ["POST", "GET"])
def studentReg():
    if request.method == "POST":
        name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(username = name, email = email).first()
        if user:
            flash("User already exists. Please login.", "error")
            return render_template("studentreg.html")

        new_user = User(username = name, email = email, password = password, role = "Student")
        db.session.add(new_user)
        db.session.commit()

        session["pending_student_user_id"] = new_user.id

        flash("Account created! now add student details", "success")
        return redirect(url_for("stud_details"))
    return render_template("studentreg.html")

@app.route('/studentreg/details', methods=["POST", "GET"])
def stud_details():
    
    user_id = session.get("pending_student_user_id")

    if not user_id:
        flash("please create student profile first", "error")
        return redirect(url_for("studentReg"))
    
    user = User.query.get(user_id)
    if not user or user.role != "Student":
        flash("Invalid registration session. please register again", "error")
        session.pop("pending_student_user_id", None)
        return redirect(url_for("studentReg"))
    
    if user.student_profile:
        flash("Student profile already exists. please login", "error")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        student_collegeid = request.form.get("student_cid")
        student_fname = request.form.get("student_fname")
        student_lname = request.form.get("student_lname")
        student_department = request.form.get("student_dept")
        student_cgpa = request.form.get("student_cgpa")
        student_batchyear = request.form.get("student_batchyear")

        if not student_fname or not student_lname or not student_department or not student_cgpa or not student_batchyear or not student_collegeid:
            flash("Please fill all student data.", "error")
            return render_template("student_details.html")

        

        new_student = Student(
            student_iid = student_collegeid,
            f_name=student_fname,
            l_name=student_lname,
            department=student_department,
            cgpa=student_cgpa,
            batch_year=student_batchyear,
            user_id=user.id
            )

        db.session.add(new_student)
        db.session.commit()

        session.pop("pending_student_user_id", None)

        flash("student registered successfully.", "success")
        return redirect(url_for("login"))
    return render_template("student_details.html")

# ---------- COMPANY DASHBOARD --------------------

@app.route('/company_dashboard')
def company_dashboard():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))

    company = Company.query.filter_by(user_id = user_id).first()
    drives = Placement_Drive.query.filter_by(company_id = company.id, status = 'Pending').all()
    closed_drives = Placement_Drive.query.filter_by(company_id = company.id, status = 'Closed').all()

    return render_template("company_dashboard.html", company=company, drives=drives, closed_drives=closed_drives)

@app.route('/company_dashboard/view_drive/<int:drive_id>')
def compview_drive(drive_id):
    drive = Placement_Drive.query.filter_by(id = drive_id).first()
    return render_template("compvdrive.html", drive=drive)

@app.route('/company_dashboard/create_drive', methods=["GET", "POST"])
def create_drive():
    user_id = session.get("id")
    if not user_id:
        flash("Please login first.", "error")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        job_title = request.form.get("job_title")
        job_description = request.form.get("job_description")
        eligibility_criteria = request.form.get("eligibility_criteria")
        application_deadline = request.form.get("application_deadline")  

        
        company = Company.query.filter_by(user_id=user_id).first()
        if not company:
            flash("Company profile not found.", "error")
            return redirect(url_for("company_dashboard"))
        
        if company.status != 'Approved':
            flash("your company is not approved yet. you cannot create drives.", "error")
            return redirect(url_for('company_dashboard'))

        deadline_dt = datetime.strptime(application_deadline, "%Y-%m-%d")

        new_drive = Placement_Drive(
            job_title=job_title,
            job_description=job_description,
            eligibility_criteria=eligibility_criteria,
            application_deadline=deadline_dt,
            company_id=company.id  
        )

        db.session.add(new_drive)
        db.session.commit()

        flash("Drive created successfully!", "success")
        return redirect(url_for("company_dashboard"))

    return render_template("create_drive.html")


@app.route('/company_dashboard/edit_drive/<int:drive_id>', methods=["GET", "POST"])
def edit_drive(drive_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))

    drive = Placement_Drive.query.filter_by(id = drive_id).first()

    if request.method == "POST":
        drive.job_title = request.form.get('job_title')
        drive.job_description = request.form.get('job_description')
        drive.eligibility_criteria = request.form.get('eligibility_criteria')
        deadline = request.form.get('application_deadline')
        drive.application_deadline = datetime.strptime(deadline, "%Y-%m-%d")

        db.session.commit()
        flash("drive updated successfully.", "success")
        return redirect(url_for('company_dashboard'))

    return render_template("edit_drive.html", drive=drive)

@app.route('/company_dashboard/close_drive/<int:drive_id>')
def close_drive(drive_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))
    drive = Placement_Drive.query.filter_by(id = drive_id).first()
    drive.status = "Closed"
    db.session.commit()
    flash("drive closed.", "success")
    return redirect(url_for('company_dashboard'))

@app.route('/company_dashboard/reopen_drive/<int:drive_id>')
def reopen_drive(drive_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))

    drive = Placement_Drive.query.filter_by(id = drive_id).first()
    drive.status = 'Pending'
    db.session.commit()
    flash("drive reopened.", "success")
    return redirect(url_for('company_dashboard'))

@app.route('/company_dashboard/delete_drive/<int:drive_id>')
def delete_drive(drive_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))
    drive = Placement_Drive.query.filter_by(id = drive_id).first()
    db.session.delete(drive)
    db.session.commit()
    flash("drive deleted.", "success")
    return redirect(url_for('company_dashboard'))

@app.route('/company_dashboard/applicants/<int:drive_id>')
def comp_view_applicants(drive_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))
    drive = Placement_Drive.query.filter_by(id = drive_id).first()
    applications = Application.query.filter_by(drive_id = drive_id).all()
    return render_template("comp_applicants.html", drive=drive, applications=applications)

@app.route('/company_dashboard/update_status/<int:app_id>/<string:status>')
def update_app_status(app_id, status):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))

    application = Application.query.filter_by(id = app_id).first()
    drive_id = application.drive_id
    application.status = status

    if status == 'Selected':
        application.student.placed = True
    elif status == 'Rejected':
        application.student.placed = False

    db.session.commit()
    flash("status updated.", "success")
    return redirect(url_for('comp_view_applicants', drive_id=drive_id))

# --------- STUDENT DASHBOARD -------------- #
@app.route('/student_dashboard')
def student_dashboard():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))

    student = Student.query.filter_by(user_id = user_id).first()

    approved_drives = Placement_Drive.query.filter_by(verified = 'Approved').all()
    company_ids = list({d.company_id for d in approved_drives})
    companies = Company.query.filter(Company.id.in_(company_ids)).all()

    my_applications = []
    if student:
        my_applications = Application.query.filter_by(student_id = student.id).all()

    return render_template("student_dashboard.html", companies=companies, my_applications=my_applications, student=student)

@app.route('/apply/<int:drive_id>')
def apply_drive(drive_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))

    student = Student.query.filter_by(user_id=user_id).first()

    existing = Application.query.filter_by(student_id=student.id, drive_id=drive_id).first()
    if existing:
        flash("Already applied to this drive.", "error")
        return redirect(url_for('student_dashboard'))

    new_app = Application(student_id=student.id, drive_id=drive_id)
    db.session.add(new_app)
    db.session.commit()

    flash("Applied successfully!", "success")
    return redirect(url_for('student_dashboard'))

@app.route('/student_dashboard/company/<int:company_id>')
def stud_view_company(company_id):
    company = Company.query.filter_by(id = company_id).first()
    drives = Placement_Drive.query.filter_by(company_id = company_id, verified = 'Approved').all()
    return render_template("student_company.html", company=company, drives=drives)

@app.route('/student_dashboard/drive/<int:drive_id>')
def stud_view_drive(drive_id):
    drive = Placement_Drive.query.filter_by(id = drive_id).first()
    user_id = session.get('id')
    student = Student.query.filter_by(user_id = user_id).first()

    already_applied = False
    if student:
        existing = Application.query.filter_by(student_id = student.id, drive_id = drive_id).first()
        if existing:
            already_applied = True

    return render_template("student_drive.html", drive=drive, already_applied=already_applied)

@app.route('/student_dashboard/history')
def stud_history():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))

    student = Student.query.filter_by(user_id = user_id).first()
    applications = []
    if student:
        applications = Application.query.filter_by(student_id = student.id).all()

    return render_template("student_history.html", student=student, applications=applications)

@app.route('/student_dashboard/edit_profile', methods=["GET", "POST"])
def stud_edit_profile():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))

    student = Student.query.filter_by(user_id = user_id).first()

    if request.method == "POST":
        student.f_name = request.form.get('f_name')
        student.l_name = request.form.get('l_name')
        student.department = request.form.get('department')
        student.cgpa = request.form.get('cgpa')
        student.batch_year = request.form.get('batch_year')

        resume = request.files.get('resume')
        if resume and resume.filename != '':
            filename = secure_filename(resume.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            resume.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            student.resume = filename

        db.session.commit()
        flash("profile updated successfully.", "success")
        return redirect(url_for('student_dashboard'))

    return render_template("stud_edit_profile.html", student=student)

# -------- admin dashboard ---------#
@app.route('/admin_dashboard')
def admin_dashboard():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))

    companies = Company.query.filter_by(status = "Approved").all()
    review_comp = Company.query.filter_by(status = "Pending").all()
    students = User.query.filter_by(role = "Student").all()
    drives = Placement_Drive.query.all()
    applications = Application.query.all()
    return render_template("admin_dashboard.html", companies=companies, students=students, drives=drives, applications=applications, review_comp=review_comp)

@app.route('/admin_dashboard/compapprov/<string:comp_name>')
def comp_approv(comp_name):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))
    comp = Company.query.filter_by(company_name=comp_name).first()
    comp.status = "Approved"
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route('/admin_dashboard/view_drive/<int:drive_id>')
def adminview_drive(drive_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))
    dr_id = Placement_Drive.query.filter_by(id = drive_id).first()

    return render_template("view_drive.html", dr_id=dr_id)

@app.route('/admin_dashboard/compblacklist/<int:user_id>')
def compblacklist(user_id):
    admin_id = session.get('id')
    if not admin_id:
        return redirect(url_for('login'))
    user = User.query.filter_by(id = user_id).first()
    user.is_blacklisted = True
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route('/admin_dashboard/remove_compblacklist/<int:user_id>')
def compremove_blacklist(user_id):
    admin_id = session.get('id')
    if not admin_id:
        return redirect(url_for('login'))
    user = User.query.filter_by(id = user_id).first()
    user.is_blacklisted = False
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route('/admin_dashboard/studblacklist/<int:user_id>')
def studblack_list(user_id):
    admin_id = session.get('id')
    if not admin_id:
        return redirect(url_for('login'))
    user = User.query.filter_by(id = user_id).first()
    user.is_blacklisted = True
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route('/admin_dashboard/remove_studblacklist/<int:user_id>')
def studremove_blacklist(user_id):
    admin_id = session.get('id')
    if not admin_id:
        return redirect(url_for('login'))
    user = User.query.filter_by(id = user_id).first()
    user.is_blacklisted = False
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.route('/admin_dashboard/compreject/<string:comp_name>')
def comp_reject(comp_name):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))
    comp = Company.query.filter_by(company_name=comp_name).first()
    comp.status = "Rejected"
    db.session.commit()
    flash("Company rejected.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route('/admin_dashboard/approve_drive/<int:drive_id>')
def approve_drive(drive_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))
    drive = Placement_Drive.query.filter_by(id=drive_id).first()
    drive.verified = "Approved"
    db.session.commit()
    flash("Drive approved.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route('/admin_dashboard/reject_drive/<int:drive_id>')
def reject_drive(drive_id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))
    drive = Placement_Drive.query.filter_by(id=drive_id).first()
    drive.verified = "Rejected"
    db.session.commit()
    flash("Drive rejected.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route('/admin_dashboard/search_students')
def search_students():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))
    q = request.args.get('q', '').strip()
    
    if q:
        students = User.query.filter(User.role == 'Student',User.username.ilike(f'%{q}%')).all()
    else:
        students = User.query.filter_by(role = 'Student').all()

    return render_template('admin_search_students.html', students=students, q=q)


@app.route('/admin_dashboard/search_companies')
def search_companies():
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))
    q = request.args.get('q', '').strip()

    if q:
        companies = Company.query.filter(Company.company_name.ilike(f'%{q}%')).all()
    else:
        companies = Company.query.all()

    return render_template('admin_search_companies.html', companies=companies, q=q)

@app.route('/admin_dashboard/delete_company/<int:user_id>')
def delete_company(user_id):
    admin_id = session.get('id')
    if not admin_id:
        return redirect(url_for('login'))
    user = User.query.filter_by(id = user_id).first()
    db.session.delete(user)
    db.session.commit()
    flash("company deleted.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_dashboard/delete_student/<int:user_id>')
def delete_student(user_id):
    admin_id = session.get('id')
    if not admin_id:
        return redirect(url_for('login'))
    user = User.query.filter_by(id = user_id).first()
    db.session.delete(user)
    db.session.commit()
    flash("student deleted.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/login', methods = ["POST", "GET"])
def login():
    

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email, password = password).first()

        if user and user.is_blacklisted:
            flash("your account has been blacklisted. contact admin.", "error")
            return redirect(url_for('login'))
        if user and user.role == "Company":
            if user.company_profile.status == "Pending":
                flash("Profile still under verification! check again later.", "error")
                return redirect(url_for('login'))
            elif user.company_profile.status == "Rejected":
                flash("Your profile has been rejected by admin! contact admin support.", "error")
                return redirect(url_for('login'))
            session['name'] = user.username
            session['id'] = user.id
            session['role'] = user.role
            
            return redirect(url_for('company_dashboard'))
        
        elif user and user.role == "Student":
            session['name'] = user.username
            session['id'] = user.id
            session['role'] = user.role
            
            return redirect(url_for('student_dashboard'))
        
        elif user and user.role == "admin":
            session['name'] = user.username
            session['id'] = user.id
            session['role'] = user.role
            return redirect(url_for('admin_dashboard'))
        
        else:
            flash("Profile not created! create a profile", "error")


    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('name', None)
    session.pop('id', None)
    session.pop('role', None)
    
    return redirect(url_for('login'))


if __name__ == "__main__":
    with app.app_context():

        db.create_all()
        existing_admin = User.query.filter_by(username="admin").first()

        if not existing_admin:
            admin_db = User(
                username="admin",
                password="admin",
                email="admin@gmail.com",
                role="admin"
            )

            db.session.add(admin_db)
            db.session.commit()

    os.makedirs('static/resumes', exist_ok=True)
    app.run(debug=True, port = 5001)


