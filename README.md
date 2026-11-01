# Skill Resume Certificate Verification System

An enterprise-grade, full-stack Python Flask web application designed for comprehensive candidate profile management, interactive multi-template resume building, secure academic & industry certificate management, human-in-the-loop verification, and compliance audit reporting.

Built with **Python 3.10+**, **Flask Application Factory**, **Flask-SQLAlchemy**, **Flask-Login**, **MySQL (via PyMySQL)**, **SQLite**, **ReportLab PDF Engine**, **Pillow**, and **Bootstrap 5**.

---

## 🌟 System Highlights & Key Features

* **Human-in-the-Loop (HITL) Certificate Verification**: No certificate is ever automatically verified. Authorized administrators review submissions against external registries, inspect documents securely, record mandatory/optional remarks, and log immutable audit trail records.
* **Interactive Resume Builder & Multi-Template PDF Generation**: Candidates can manage education, work experience, technical skills, soft skills, projects, and achievements, then export a high-resolution PDF resume in **Modern**, **Executive**, or **Minimal** templates using ReportLab.
* **Skill Taxonomy & Certificate Linking**: Technical and soft skills can be directly linked to verified certificates, displaying verified credential badges across resumes and candidate profiles.
* **Public Candidate Discovery Directory**: Recruiters and evaluators can search and filter verified candidates by name, specific skills, qualification, and verified credentials at `/candidates`.
* **Administrative Governance & Real-time Analytics**: Admin dashboard with Chart.js doughnut and bar charts, user management directory with active status toggles, verification history audit trail, date-filtered metrics, CSV export, and PDF audit compliance reports.
* **Multi-Layered Security Architecture**: Strict Role-Based Access Control (`job_seeker` vs `admin`), Werkzeug password hashing, session-bound CSRF protection, secure timed token password recovery (`itsdangerous`), 16MB file size limits, MIME type inspection, cryptographic filename sanitization, and access-controlled document serving.

---

## 📚 Complete Documentation Suite

Comprehensive technical and operational documentation is available in the [`docs/`](docs/) directory:

1. [**System Architecture Documentation**](docs/architecture.md) - Deep dive into Application Factory, Blueprints, Security Model, and ReportLab PDF compilation.
2. [**Database Schema Documentation**](docs/database_schema.md) - Entity-Relationship diagram, 9 relational tables, columns, indexes, foreign keys, and migration strategy.
3. [**Application Workflow Documentation**](docs/application_workflow.md) - Sequence diagrams and lifecycle workflows for Registration, Verification, Resume Building, and Directory Discovery.
4. [**Installation & Setup Guide**](docs/installation_guide.md) - Step-by-step setup on Windows, macOS, and Linux for SQLite and MySQL.
5. [**Testing & Verification Report**](docs/testing_report.md) - Full audit of automated test suites, pass/fail status, and coverage metrics.
6. [**Administrator User Guide**](docs/admin_user_guide.md) - Operating manual for platform administration, verification review, and report generation.
7. [**Job Seeker User Guide**](docs/job_seeker_user_guide.md) - Candidate guide for profile management, resume building, and certificate submissions.

---

## 📂 Project Directory Structure

```text
skillresumecertificate/
├── app/
│   ├── __init__.py            # Application factory, public candidate directory (/candidates), health check
│   ├── models.py              # 9 SQLAlchemy models (User, Profile, Education, Skill, Resume, Certificate, etc.)
│   ├── extensions.py          # SQLAlchemy, Flask-Login, built-in CSRF protection
│   ├── auth/                  # Authentication Blueprint (Register, Login, Logout, Password Change & Reset)
│   ├── seeker/                # Job Seeker Portal (Profile CRUD, Resume Builder, Certificate Management)
│   ├── admin/                 # Administrator Governance (Users Directory, Status Toggle, Audit Log)
│   ├── verification/          # Human Reviewer Queue (Pending queue, Document viewing, Approval/Rejection)
│   ├── reports/               # Analytics & Reporting (Longitudinal charts, CSV export, PDF Report)
│   ├── utils/                 # Utilities (Multi-template PDF generator, Report PDF engine, DB migration)
│   ├── templates/             # Jinja2 templates styled with modern Navy & Teal Bootstrap 5 design
│   ├── static/                # CSS custom design system, JavaScript helpers, and icons
│   └── uploads/               # Isolated storage for resumes, certificates, and profile photos
├── docs/                      # Complete technical, architectural, and user documentation
├── tests/                     # Automated unittest suite (test_workflow.py)
├── config.py                  # Environment-driven database and application configurations
├── run.py                     # Application execution entrypoint
├── requirements.txt           # Pinned Python package dependencies
├── .env.example               # Environment configuration template
└── .gitignore                 # Enterprise Git exclusion rules protecting secrets and uploads
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
* Python 3.10 or higher
* Windows PowerShell, macOS Terminal, or Linux Bash

### 2. Activate Virtual Environment
* **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

### 5. Initialize Database & Run Migrations
```bash
python app/utils/migrate_db.py
```

### 6. Start the Web Application
```bash
python run.py
```
Access the application at `http://127.0.0.1:5000`.

---

## 🔑 Evaluation Credentials

| Role | Username / Identifier | Email | Password | Access Capabilities |
|---|---|---|---|---|
| **Administrator** | `admin` | `admin@skillverify.com` | `admin123` | Full Admin Dashboard, Verification Queue, User Directory, Reports & Audit Log |
| **Job Seeker** | `test_seeker` | `seeker@example.com` | `Password123!` | Job Seeker Portal, Resume Builder, Certificate Upload, Profile Management |
| **Job Seeker** | `sarah_seeker` | `sarah_seeker@example.com` | `Password123!` | Secondary test candidate account |

---

## 🧪 Automated Testing

Execute the comprehensive automated test suite (6 major suites covering 42 assertions):
```bash
python -m unittest tests/test_workflow.py
```
All tests pass cleanly (`OK`, 0 errors, 0 failures).

---

## 🌐 Azure Repos and Git Push Instructions

To push the project to Azure Repos or GitHub:

1. **Verify Git Installation**:
   Ensure Git is installed on your workstation (`git --version`). If not installed, download from [git-scm.com](https://git-scm.com/).
2. **Initialize Repository** (if not already initialized):
   ```bash
   git init
   ```
3. **Stage Changes**:
   ```bash
   git add .
   ```
   *(Notice that `.env`, `venv/`, `instance/`, `*.db`, and uploaded private files in `app/uploads/` are automatically excluded by `.gitignore`)*
4. **Commit with Meaningful Message**:
   ```bash
   git commit -m "Complete Skill Resume Certificate Verification platform with HITL verification, multi-template resumes, and compliance reports"
   ```
5. **Link Azure DevOps Remote & Push**:
   ```bash
   git remote add origin https://<organization>@dev.azure.com/<organization>/<project>/_git/<repository>
   git branch -M main
   git push -u origin main
   ```
