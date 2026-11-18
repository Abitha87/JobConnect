
# JobConnect – Job Portal Web Application

## 1. Project Overview

JobConnect is a web-based job portal application developed using Python Flask. It provides a platform where job seekers can explore job opportunities and apply for jobs, while employers can post job openings and manage applications.

The application also includes an administrator dashboard to manage registered users and job postings.

## 2. Features

### 2.1 User Authentication
- User registration and login.
- Role-based access for Job Seekers, Employers and Admin.
- Secure session management.
- Logout functionality.

### 2.2 Job Seeker
- View available job opportunities.
- Search and filter jobs.
- Apply for jobs by uploading a PDF resume.
- Track application status.
- View submitted applications.

### 2.3 Employer
- Post new job openings.
- View and manage posted jobs.
- View applications received for each job.
- Download candidate resumes.
- Update application status.

### 2.4 Admin
- View total users, job seekers and employers.
- View total job postings.
- Manage registered users.
- Manage job listings.

## 3. Technologies Used

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, Bootstrap 5 |
| Backend | Python, Flask |
| Database | SQLite |
| ORM | Flask-SQLAlchemy |
| Authentication | Flask-Login |
| Template Engine | Jinja2 |

## 4. Project Structure

```text
jobconnect/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── jobs.html
│   ├── post_job.html
│   ├── my_jobs.html
│   ├── my_applications.html
│   ├── applications.html
│   └── admin_dashboard.html
│
├── static/
│   └── css/
│       └── style.css
│
├── uploads/
│
└── instance/
```

Note: The structure is illustrative. Update it if your actual project folders are different.

## 5. Installation and Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/Abitha87/JobConnect.git
```

### Step 2: Navigate to the Project Folder

```bash
cd jobconnect
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

### Step 4: Activate the Virtual Environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 5: Install Required Packages

```bash
pip install -r requirements.txt
```

### Step 6: Run the Application

```bash
python app.py
```

### Step 7: Open the Application

Open your web browser and visit:

http://127.0.0.1:5000/

## 6. Application Modules

1. Authentication Module
2. Job Management Module
3. Job Application Module
4. Resume Upload Module
5. Employer Management Module
6. Admin Management Module

## 7. Future Enhancements

- Email notifications for application updates.
- Advanced job recommendation system.
- Online deployment.
- Integration with external job listing APIs.

## 8. Author

**Abitha Shanmugam**

B.Tech – Artificial Intelligence and Data Science

## 9. Project Title

**JobConnect – Job Portal Web Application**
