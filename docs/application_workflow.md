# Application Workflow Documentation

**Skill Resume Certificate Verification System**

---

## 1. Candidate Registration & Authentication Workflow

```mermaid
sequenceDiagram
    autonumber
    actor Candidate as Job Seeker
    participant Web as Web Interface
    participant Auth as Auth Blueprint
    participant DB as SQLite / MySQL DB

    Candidate->>Web: Navigate to /auth/register
    Web-->>Candidate: Display Registration Form (Job Seeker Role Enforced)
    Candidate->>Auth: Submit username, email, password, name
    Auth->>Auth: Validate password strength, confirm match, unique email/username
    Auth->>DB: INSERT into users (role='job_seeker') & job_seeker_profiles
    Auth-->>Candidate: Flash success & Redirect to /auth/login
    Candidate->>Auth: Submit credentials
    Auth->>Auth: Verify Werkzeug password hash
    Auth->>DB: Load session & user profile
    Auth-->>Candidate: Authenticated Session -> Redirect to /seeker/dashboard
```

### Password Recovery Workflow
1. User clicks **"Forgot password?"** on the login page (`/auth/forgot-password`).
2. Enters registered email address.
3. System generates a secure `itsdangerous` timed cryptographic token (30-minute validity) and generates a reset link (`/auth/reset-password/<token>`).
4. User accesses the link, specifies a new compliant password, and the system hashes and updates `users.password_hash`.

---

## 2. Certificate Upload & Human-in-the-Loop Verification Workflow

The core USP of the platform is that **no certificate is ever automatically verified**. Every credential must undergo manual human-in-the-loop review by an authorized administrator.

```mermaid
sequenceDiagram
    autonumber
    actor Seeker as Job Seeker
    actor Admin as Platform Administrator
    participant SeekerBP as Seeker Module
    participant VerifBP as Verification Module
    participant Storage as Uploads Storage
    participant DB as Database
    participant Notif as Notification Engine

    Seeker->>SeekerBP: Submit Certificate (Title, Org, Dates, Credential ID, File)
    SeekerBP->>SeekerBP: Validate extension (PDF/JPG/PNG), MIME type, size <= 16MB
    SeekerBP->>Storage: Store file as cert_{profile_id}_{uuid}_{filename}
    SeekerBP->>DB: INSERT Certificate (status='pending')
    SeekerBP-->>Seeker: Flash success ("Status: Pending Admin Review")

    Note over Admin,VerifBP: Administrator Review Cycle
    Admin->>VerifBP: Access /verification/queue
    VerifBP->>DB: Query certificates WHERE status='pending'
    VerifBP-->>Admin: Display Pending Verification Queue
    Admin->>VerifBP: Click "View Document" (Secure route /verification/<id>/view)
    VerifBP->>Storage: Serve file safely via send_from_directory
    Admin->>VerifBP: Submit Review Decision (Action='verified'|'rejected', Remarks)
    
    VerifBP->>DB: UPDATE Certificate (status=action, verified_at=NOW(), verified_by_id=Admin.id)
    VerifBP->>DB: INSERT VerificationRecord (audit trail entry)
    VerifBP->>Notif: Create Notification for Candidate
    Notif->>DB: INSERT Notification (user_id=Candidate.id, message=Decision details)
    VerifBP-->>Admin: Flash confirmation & Refresh queue
```

---

## 3. Resume Management & Multi-Template PDF Generation

```mermaid
graph TD
    A[Job Seeker Portal] --> B{Resume Management Action}
    
    B -->|Interactive Builder| C[Resume Builder Form]
    C --> C1[Add / Edit Education]
    C --> C2[Add / Edit Technical & Soft Skills]
    C --> C3[Link Skills to Verified Certificates]
    C --> C4[Add / Edit Work Experience & Projects]
    C --> C5[Save to Database]
    
    B -->|Upload Existing| D[Upload PDF / DOCX Resume]
    D --> D1[Validate File Type & Size]
    D --> D2[Save to app/uploads/resumes/]
    
    B -->|Preview & PDF| E[Resume Preview Canvas]
    E --> F{Select Design Template}
    F -->|Modern| G1[Teal Accent & Centered Header]
    F -->|Executive| G2[Navy Corporate & Left-Aligned Header]
    F -->|Minimal| G3[Monochrome Technical & Compact Layout]
    
    G1 --> H[ReportLab Dynamic Compilation Engine]
    G2 --> H
    G3 --> H
    H --> I[Downloadable High-Res PDF Resume]
```

---

## 4. Candidate Discovery Directory Workflow

```mermaid
graph LR
    Visitor([Public Visitor / Recruiter / Admin]) --> Direct[/candidates]
    Direct --> Filters[Search & Filter Parameters]
    Filters --> F1[Candidate Name Keyword]
    Filters --> F2[Skill Search e.g. Python, Docker]
    Filters --> F3[Degree / Institution Search]
    Filters --> F4[Verified Credentials Only Toggle]
    
    Filters --> Results[Candidate Grid Cards]
    Results --> ProfileView[Public Candidate Profile /candidates/:id]
    ProfileView --> V1[Verified Certificate Badges]
    ProfileView --> V2[Education & Experience History]
    ProfileView --> V3[Categorized Skills]
```
