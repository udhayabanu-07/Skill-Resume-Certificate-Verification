# Installation and Setup Guide

**Skill Resume Certificate Verification System**

---

## 1. System Requirements

* **Python**: Version 3.10 or higher.
* **Operating System**: Windows 10/11, macOS 12+, or Ubuntu/Debian Linux.
* **Database Engine**:
  * SQLite (default for development; requires no external services).
  * MySQL 8.0+ or MariaDB 10.5+ (optional for enterprise deployments).
* **Disk Space**: At least 500 MB for Python environment and document uploads.

---

## 2. Step-by-Step Installation

### Step 1: Open the Project Directory
Open your terminal (PowerShell on Windows, Terminal on macOS/Linux) and navigate to the project directory:
```bash
cd skillresumecertificate
```

### Step 2: Create and Activate a Virtual Environment
* **On Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
  *(If PowerShell script execution is restricted, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

* **On macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Step 3: Install Required Dependencies
Install the pinned libraries via `requirements.txt`:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Verified installed dependencies:
* `Flask >= 3.1.0` (Core WSGI framework)
* `Flask-SQLAlchemy >= 3.1.1` (Relational ORM)
* `Flask-Login >= 0.6.3` (Session & authentication)
* `PyMySQL >= 1.2.0` (MySQL connector)
* `Werkzeug >= 3.1.0` (Security & password hashing)
* `python-dotenv >= 1.0.0` (Environment variable loader)
* `reportlab >= 5.0.0` (PDF document generator)
* `email-validator >= 2.3.0` (Email syntax validation)
* `Pillow >= 11.0.0` (Image processing & photo validation)

### Step 4: Configure Environment Variables
Copy the `.env.example` template into `.env`:
* **On Windows (PowerShell):**
  ```powershell
  Copy-Item .env.example .env
  ```
* **On macOS / Linux:**
  ```bash
  cp .env.example .env
  ```

Inspect `.env` and configure key variables:
```env
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=skillverify-super-secret-key-change-in-production

# Default SQLite Configuration (local)
DATABASE_URL=sqlite:///instance/skill_verify.db

# Upload limits
MAX_CONTENT_LENGTH=16777216
```

### Step 5: Initialize the Database
Run the migration utility to ensure all database tables and new columns are present:
```bash
python app/utils/migrate_db.py
```

### Step 6: Launch the Web Application
Start the development server:
```bash
python run.py
```
The application will start on:
```
http://127.0.0.1:5000
```

Verify system health by accessing:
```
http://127.0.0.1:5000/health
```

---

## 3. Switching to MySQL (Production Database)

To configure the application with MySQL instead of SQLite:

1. Create a MySQL database and user:
   ```sql
   CREATE DATABASE skill_verify_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'skill_admin'@'localhost' IDENTIFIED BY 'StrongPassword123!';
   GRANT ALL PRIVILEGES ON skill_verify_db.* TO 'skill_admin'@'localhost';
   FLUSH PRIVILEGES;
   ```
2. In your `.env` file, update `DATABASE_URL`:
   ```env
   DATABASE_URL=mysql+pymysql://skill_admin:StrongPassword123!@localhost:3306/skill_verify_db
   ```
3. Initialize the schema:
   ```bash
   python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
   ```

---

## 4. Default Credentials for Evaluation

| Role | Username / Identifier | Email | Password |
|---|---|---|---|
| **Administrator** | `admin` | `admin@skillverify.com` | `admin123` |
| **Job Seeker** | `test_seeker` | `seeker@example.com` | `Password123!` |
| **Job Seeker** | `sarah_seeker` | `sarah_seeker@example.com` | `Password123!` |
