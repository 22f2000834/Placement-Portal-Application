# Placement Portal

A Flask-based placement management web application for coordinating campus recruitment activities between **students**, **companies**, and an **admin** user. The system allows companies to register and post placement drives, students to apply for verified drives, and admins to manage users, companies, and drive approvals.

## Features

### Admin
- View overall platform statistics from the admin dashboard
- Approve or reject company registrations
- Approve or reject placement drives
- Search registered students and companies
- Blacklist or restore student and company accounts
- Delete student and company profiles

### Company
- Register and submit company profile details
- Wait for admin verification before accessing company features
- Create, edit, close, reopen, and delete placement drives
- View applicants for each drive
- Update student application statuses

### Student
- Register and complete a student profile
- Upload and update resume information
- View verified placement drives
- Apply to eligible drives
- View company details and drive details
- Track application history
- Edit profile details

## Tech Stack

- **Backend:** Python, Flask
- **Database:** SQLite
- **ORM:** Flask-SQLAlchemy / SQLAlchemy
- **Frontend:** HTML, CSS, Jinja2 templates
- **File Uploads:** Werkzeug secure file handling for resumes

## Project Structure

```text
.
├── app.py                     # Main Flask application, routes, and database models
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── instance/
│   └── placement.db           # SQLite database file
├── static/
│   └── resumes/               # Uploaded student resumes
└── templates/                 # HTML templates
    ├── base.html
    ├── login.html
    ├── admin_dashboard.html
    ├── company_dashboard.html
    ├── student_dashboard.html
    └── ...
```

## Getting Started

### Prerequisites

Make sure you have the following installed:

- Python 3.10 or later
- pip
- Git

### Installation

1. Clone the repository:

```bash
git clone <your-repository-url>
cd <your-project-folder>
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
```

On macOS/Linux:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set a secret key for sessions:

On macOS/Linux:

```bash
export SECRET_KEY="your-secret-key"
```

On Windows PowerShell:

```powershell
$env:SECRET_KEY="your-secret-key"
```

5. Run the application:

```bash
python app.py
```

6. Open the app in your browser:

```text
http://127.0.0.1:5001
```

## Default Admin Login

When the application starts, it creates a default admin account if one does not already exist.

```text
Email: admin@gmail.com
Password: admin
```

> For production use, change the default admin credentials and avoid storing plain-text passwords.

## Database Models

The application uses the following main models:

- **User**: Stores login credentials, role, account status, and profile relationship
- **Company**: Stores company profile details and verification status
- **Student**: Stores student profile details, CGPA, department, batch year, and resume path
- **Placement_Drive**: Stores job posting details, eligibility criteria, deadlines, and approval status
- **Application**: Tracks student applications to placement drives and application status

## Main Routes

| Route | Description |
| --- | --- |
| `/` | Landing page |
| `/login` | User login |
| `/logout` | User logout |
| `/companyreg` | Company registration |
| `/companyreg/details` | Company profile details |
| `/studentreg` | Student registration |
| `/studentreg/details` | Student profile details |
| `/company_dashboard` | Company dashboard |
| `/company_dashboard/create_drive` | Create a placement drive |
| `/student_dashboard` | Student dashboard |
| `/student_dashboard/history` | Student application history |
| `/admin_dashboard` | Admin dashboard |
| `/admin_dashboard/search_students` | Search students |
| `/admin_dashboard/search_companies` | Search companies |

## Typical Workflow

1. A company registers and submits company details.
2. The admin reviews and approves or rejects the company.
3. An approved company creates placement drives.
4. The admin verifies placement drives.
5. Students browse verified drives and apply.
6. Companies review applicants and update application statuses.
7. Students track their application history.

## Configuration Notes

- The SQLite database is configured as `sqlite:///placement.db`, which Flask stores inside the `instance/` folder by default.
- Uploaded resumes are stored in `static/resumes/`.
- The app runs in debug mode on port `5001` when launched with `python app.py`.
- Session security uses the `SECRET_KEY` environment variable, with a fallback development key in `app.py`.

## Security Improvements Recommended

Before deploying this project, consider the following improvements:

- Hash passwords using a library such as Werkzeug security helpers or Flask-Bcrypt
- Replace the default admin credentials
- Disable debug mode in production
- Add role-based authorization checks to protected routes
- Validate uploaded resume file types and file sizes
- Move sensitive configuration into environment variables
- Add CSRF protection for forms

## Future Enhancements

- Email notifications for company approvals, drive approvals, and application updates
- Advanced student eligibility matching based on CGPA, department, and batch year
- Resume preview and download controls for companies
- Admin analytics for placement statistics
- Pagination and filters for large student, company, and drive lists
- Password reset and account recovery flow


