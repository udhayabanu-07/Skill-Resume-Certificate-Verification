# Database Schema Documentation

**Skill Resume Certificate Verification System**

---

## 1. Entity-Relationship Overview

The relational database architecture is modeled using SQLAlchemy ORM to ensure consistency, referential integrity, and cross-database compatibility (SQLite and MySQL).

```mermaid
erDiagram
    User ||--o| JobSeekerProfile : "has profile"
    User ||--o{ Notification : "receives"
    User ||--o{ Certificate : "verified by"
    User ||--o{ VerificationRecord : "reviewed by"
    
    JobSeekerProfile ||--o{ Education : "has education"
    JobSeekerProfile ||--o{ Skill : "possesses"
    JobSeekerProfile ||--o{ WorkExperience : "has experience"
    JobSeekerProfile ||--o{ Resume : "uploads/builds"
    JobSeekerProfile ||--o{ Certificate : "uploads"

    Certificate ||--o{ VerificationRecord : "audited by"
    Certificate ||--o{ Skill : "validates"

    User {
        int id PK
        string username UK
        string email UK
        string password_hash
        string role "job_seeker | admin"
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    JobSeekerProfile {
        int id PK
        int user_id FK, UK
        string first_name
        string last_name
        string phone
        date date_of_birth
        string address
        string city
        string state
        string country
        text bio
        text career_objective
        string linkedin_url
        string github_url
        string portfolio_url
        string profile_picture
        datetime created_at
        datetime updated_at
    }

    Education {
        int id PK
        int profile_id FK
        string institution
        string degree
        string field_of_study
        string grade
        date start_date
        date end_date
        boolean is_current
        text description
    }

    Skill {
        int id PK
        int profile_id FK
        string name
        string category "technical | soft"
        string proficiency_level "beginner | intermediate | advanced | expert"
        float years_of_experience
        int certificate_id FK, nullable
    }

    WorkExperience {
        int id PK
        int profile_id FK
        string company
        string position
        string location
        date start_date
        date end_date
        boolean is_current
        text description
    }

    Resume {
        int id PK
        int profile_id FK
        string title
        string original_filename
        string stored_filename
        string file_path
        int file_size
        string file_type "pdf | docx"
        boolean is_primary
        datetime uploaded_at
    }

    Certificate {
        int id PK
        int profile_id FK
        string title
        string issuing_organization
        string credential_id
        string credential_url
        date issue_date
        date expiration_date
        string original_filename
        string stored_filename
        string file_path
        int file_size
        string mime_type
        string status "pending | verified | rejected"
        datetime verified_at
        int verified_by_id FK, nullable
        datetime uploaded_at
    }

    VerificationRecord {
        int id PK
        int certificate_id FK
        int reviewer_id FK
        string action "verified | rejected"
        text remarks
        datetime reviewed_at
    }

    Notification {
        int id PK
        int user_id FK
        string title
        text message
        boolean is_read
        datetime created_at
    }
```

---

## 2. Table Specifications

### 2.1 `users`
Stores user identities, login credentials, and roles.
* `id` (INTEGER, Primary Key, Auto Increment)
* `username` (VARCHAR(80), Unique, Not Null, Indexed)
* `email` (VARCHAR(120), Unique, Not Null, Indexed)
* `password_hash` (VARCHAR(256), Not Null) - Werkzeug salted hash
* `role` (VARCHAR(20), Not Null, Default `'job_seeker'`) - Values: `'job_seeker'`, `'admin'`
* `is_active` (BOOLEAN, Not Null, Default `True`) - Account status toggle
* `created_at` (DATETIME, Default `CURRENT_TIMESTAMP`)
* `updated_at` (DATETIME, On Update `CURRENT_TIMESTAMP`)

### 2.2 `job_seeker_profiles`
Contains profile and biographical information for Job Seekers.
* `id` (INTEGER, Primary Key, Auto Increment)
* `user_id` (INTEGER, Foreign Key `users.id` ON DELETE CASCADE, Unique, Not Null)
* `first_name` (VARCHAR(50), Not Null)
* `last_name` (VARCHAR(50), Not Null)
* `phone` (VARCHAR(20), Nullable)
* `date_of_birth` (DATE, Nullable)
* `address` (VARCHAR(200), Nullable)
* `city` (VARCHAR(100), Nullable)
* `state` (VARCHAR(100), Nullable)
* `country` (VARCHAR(100), Nullable)
* `bio` (TEXT, Nullable)
* `career_objective` (TEXT, Nullable)
* `linkedin_url` (VARCHAR(255), Nullable)
* `github_url` (VARCHAR(255), Nullable)
* `portfolio_url` (VARCHAR(255), Nullable)
* `profile_picture` (VARCHAR(255), Nullable)
* `created_at` (DATETIME, Default `CURRENT_TIMESTAMP`)
* `updated_at` (DATETIME, On Update `CURRENT_TIMESTAMP`)

**Dynamic Property:** `profile_completion_percentage`:
Calculates real-time profile completion based on weighted scores: First/Last Name (20%), Phone (10%), Location (10%), Career Objective/Bio (15%), LinkedIn/GitHub (10%), Education Entry (15%), Skill Entry (10%), Profile Photo (10%).

### 2.3 `skills`
Catalog of technical and interpersonal capabilities.
* `id` (INTEGER, Primary Key, Auto Increment)
* `profile_id` (INTEGER, Foreign Key `job_seeker_profiles.id` ON DELETE CASCADE, Not Null)
* `name` (VARCHAR(100), Not Null)
* `category` (VARCHAR(20), Default `'technical'`) - Values: `'technical'`, `'soft'`
* `proficiency_level` (VARCHAR(20), Default `'intermediate'`) - Values: `'beginner'`, `'intermediate'`, `'advanced'`, `'expert'`
* `years_of_experience` (FLOAT, Default 0.0)
* `certificate_id` (INTEGER, Foreign Key `certificates.id` ON DELETE SET NULL, Nullable)

### 2.4 `certificates`
Credential documents submitted by candidates for verification.
* `id` (INTEGER, Primary Key, Auto Increment)
* `profile_id` (INTEGER, Foreign Key `job_seeker_profiles.id` ON DELETE CASCADE, Not Null)
* `title` (VARCHAR(200), Not Null)
* `issuing_organization` (VARCHAR(200), Not Null)
* `credential_id` (VARCHAR(100), Nullable)
* `credential_url` (VARCHAR(255), Nullable)
* `issue_date` (DATE, Nullable)
* `expiration_date` (DATE, Nullable)
* `original_filename` (VARCHAR(255), Not Null)
* `stored_filename` (VARCHAR(255), Unique, Not Null)
* `file_path` (VARCHAR(500), Not Null)
* `file_size` (INTEGER, Not Null)
* `mime_type` (VARCHAR(100), Not Null)
* `status` (VARCHAR(20), Default `'pending'`, Indexed) - Values: `'pending'`, `'verified'`, `'rejected'`
* `verified_at` (DATETIME, Nullable)
* `verified_by_id` (INTEGER, Foreign Key `users.id` ON DELETE SET NULL, Nullable)
* `uploaded_at` (DATETIME, Default `CURRENT_TIMESTAMP`)

### 2.5 `verification_records`
Immutable audit log recording every administrative decision.
* `id` (INTEGER, Primary Key, Auto Increment)
* `certificate_id` (INTEGER, Foreign Key `certificates.id` ON DELETE CASCADE, Not Null)
* `reviewer_id` (INTEGER, Foreign Key `users.id` ON DELETE RESTRICT, Not Null)
* `action` (VARCHAR(20), Not Null) - Values: `'verified'`, `'rejected'`
* `remarks` (TEXT, Nullable)
* `reviewed_at` (DATETIME, Default `CURRENT_TIMESTAMP`)

### 2.6 `notifications`
In-app candidate and administrator notification center.
* `id` (INTEGER, Primary Key, Auto Increment)
* `user_id` (INTEGER, Foreign Key `users.id` ON DELETE CASCADE, Not Null)
* `title` (VARCHAR(150), Not Null)
* `message` (TEXT, Not Null)
* `is_read` (BOOLEAN, Default `False`)
* `created_at` (DATETIME, Default `CURRENT_TIMESTAMP`)

---

## 3. Migration Strategy & Compatibility

To preserve existing user records and support SQLite alongside MySQL:
1. `app/utils/migrate_db.py` inspects table schemas dynamically using `PRAGMA table_info` and executes non-destructive `ALTER TABLE ADD COLUMN` queries.
2. Production MySQL environments automatically utilize equivalent DDL statements via SQLAlchemy.
