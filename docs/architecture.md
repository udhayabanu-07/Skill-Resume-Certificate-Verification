# System Architecture Documentation

**Skill Resume Certificate Verification System**

---

## 1. Executive Architecture Overview

The **Skill Resume Certificate Verification System** is designed following enterprise software engineering principles using Python 3.10+, Flask, and SQLAlchemy ORM. The platform implements a **Human-in-the-Loop (HITL) Certificate Verification Architecture**, ensuring that no academic or professional credential is authenticated without verifiable audit logs and authorized administrator review.

```mermaid
graph TD
    User([End User / Web Browser]) -->|HTTP / HTTPS| NGINX[Reverse Proxy / Web Server]
    NGINX -->|WSGI / Local Server| FlaskApp[Flask Application Factory]
    
    subgraph Core Application Architecture
        FlaskApp --> AuthBP[Auth Blueprint<br/>/auth/*]
        FlaskApp --> SeekerBP[Job Seeker Blueprint<br/>/seeker/*]
        FlaskApp --> AdminBP[Admin Blueprint<br/>/admin/*]
        FlaskApp --> VerifBP[Verification Blueprint<br/>/verification/*]
        FlaskApp --> ReportsBP[Reports Blueprint<br/>/reports/*]
        FlaskApp --> MainBP[Public & Discovery Blueprint<br/>/ & /candidates/*]
    end

    subgraph Security & Access Layer
        AuthBP --> RBAC[Role-Based Access Control<br/>@login_required, @admin_required, @seeker_required]
        SeekerBP --> CSRF[CSRF Protection & Token Validation]
        AdminBP --> AuditLogger[Immutable VerificationRecord Audit Trail]
    end

    subgraph Storage & Services
        FlaskApp --> SQLAlchemy[SQLAlchemy ORM Layer]
        SQLAlchemy --> SQLite[(SQLite Local DB)]
        SQLAlchemy -.-> MySQL[(MySQL / PyMySQL Production DB)]
        
        SeekerBP --> SecureStorage[Secure File System Storage<br/>app/uploads/{resumes, certificates, profiles}]
        ReportsBP --> ReportLabGen[ReportLab PDF Engine<br/>Resume & Audit Report Generation]
    end
```

---

## 2. Directory & Blueprint Structure

The system is organized into modular Blueprints, keeping separation of concerns clean and maintainable:

```
skillresumecertificate/
├── app/
│   ├── __init__.py               # Application factory & public routes (/candidates, /health)
│   ├── models.py                 # SQLAlchemy relational data models (9 core entities)
│   ├── extensions.py             # Shared Flask extension instances (db, login_manager)
│   ├── auth/                     # Authentication & credential recovery
│   │   ├── __init__.py
│   │   └── routes.py             # Login, register, logout, password change & reset
│   ├── seeker/                   # Candidate profile, resume & certificate management
│   │   ├── __init__.py
│   │   └── routes.py             # Profile CRUD, resume builder, cert upload & edit
│   ├── admin/                    # Platform administration & user governance
│   │   ├── __init__.py
│   │   └── routes.py             # User directory, account status toggles, audit views
│   ├── verification/             # Dedicated human-in-the-loop review workflow
│   │   ├── __init__.py
│   │   └── routes.py             # Pending queue, approval, rejection, remarks
│   ├── reports/                  # Analytics and compliance reporting
│   │   ├── __init__.py
│   │   └── routes.py             # Longitudinal metrics, Chart.js, CSV & PDF export
│   ├── utils/                    # Core utility services
│   │   ├── pdf_generator.py      # Multi-template resume PDF engine (Modern, Executive, Minimal)
│   │   ├── report_pdf.py         # Executive audit & statistics PDF report engine
│   │   └── migrate_db.py         # Zero-loss SQLite migration automation
│   ├── templates/                # Jinja2 responsive templates (Bootstrap 5)
│   │   ├── base.html             # Master layout with brand navy/teal design & notification bell
│   │   ├── auth/                 # Login, register, forgot/reset password templates
│   │   ├── seeker/               # Profile view/edit, resume builder/preview, cert edit
│   │   ├── admin/                # Admin dashboard, users directory, user detail, audit log
│   │   ├── verification/         # Verification queue and certificate inspection modal
│   │   ├── reports/              # Reports dashboard with Chart.js charts
│   │   ├── candidates/           # Verified candidate discovery directory & public profiles
│   │   └── notifications/        # In-app notification center
│   ├── static/                   # Static assets
│   │   ├── css/style.css         # Modern Navy & Teal design system
│   │   └── js/main.js            # Client-side validation, toast notifications, UI helpers
│   └── uploads/                  # Protected storage with .gitkeep placeholders
│       ├── certificates/         # Encrypted/hashed candidate certificates
│       ├── profiles/             # Candidate avatar photographs
│       └── resumes/              # Uploaded PDF/DOCX resumes
├── config.py                     # Environment-driven configuration (Development, Production, Testing)
├── run.py                        # Entry point script
├── requirements.txt              # Pinned Python package dependencies
├── .env.example                  # Environment configuration template
└── .gitignore                    # Git exclusions protecting secrets and private files
```

---

## 3. Security Architecture & Threat Mitigation

### 3.1 Role-Based Access Control (RBAC)
- **Roles**: `job_seeker` and `admin`.
- Public registration strictly forces the `job_seeker` role. No user can escalate their privileges during registration.
- Route decorators enforce authorization:
  - `@login_required`: Requires authenticated session.
  - `@admin_required`: Restricts routes exclusively to active administrators.
  - `@seeker_required`: Restricts candidate tools to job seekers.
- Candidate privacy enforcement: Job seekers can only view, edit, or delete their own resumes, certificates, and profiles.

### 3.2 Secure Credential Management
- Passwords hashed using Werkzeug (`scrypt` / `pbkdf2:sha256` with unique cryptographically random salts).
- Forgot password workflow utilizes signed, time-limited cryptographic tokens (`itsdangerous.URLSafeTimedSerializer`) expiring after 30 minutes.

### 3.3 Secure File Upload Pipeline
1. **Extension Whitelisting**: Strictly restricts uploads to `.pdf`, `.png`, `.jpg`, `.jpeg` for certificates and `.pdf`, `.docx` for resumes.
2. **MIME Type Validation**: Re-checks `file.mimetype` against accepted MIME types.
3. **Payload Size Limits**: Enforces 16 MB maximum content length (`MAX_CONTENT_LENGTH`). Empty files (0 bytes) are rejected immediately.
4. **Filename Sanitization**: Uploaded files are renamed using secure random strings:
   `cert_{profile_id}_{uuid.uuid4().hex[:12]}_{secure_filename(orig)}`
   This prevents directory traversal attacks, filename collisions, and malicious overwrites.
5. **Private Document Protection**: Upload directories are placed outside public static routes. Files are served strictly via authenticated Flask handlers (`send_from_directory`) with permission validation.

---

## 4. Database Architecture & Portability

The database layer utilizes SQLAlchemy ORM, ensuring strict decoupling from underlying SQL engines:
- **Local Development**: SQLite (`instance/skill_verify.db`), zero configuration required.
- **Production Deployment**: MySQL via `PyMySQL` driver (`mysql+pymysql://user:pass@host:port/dbname`).
- Relationships feature foreign key constraints, cascade rules, and indexes on critical query paths (e.g., `user_id`, `profile_id`, `status`).

---

## 5. ReportLab PDF Generation Architecture

The application includes two specialized PDF generators:
1. **Resume PDF Engine (`app/utils/pdf_generator.py`)**:
   - Generates pixel-perfect resumes on Letter canvas using ReportLab `SimpleDocTemplate` and flowables (`Paragraph`, `Table`, `Spacer`, `HRFlowable`).
   - Supports 3 visual templates:
     - `modern`: Teal accents, centered header, structured divider lines.
     - `executive`: Navy brand styling, left-aligned executive header, bold typography.
     - `minimal`: Clean monochrome, compact typography for technical CVs.
   - Highlights verified credentials with a green badge and verification metadata.
2. **Platform Audit PDF Engine (`app/utils/report_pdf.py`)**:
   - Compiles executive compliance reports including user registration counts, certificate verification totals, pass rates, and the 20 most recent administrative audit decisions.
