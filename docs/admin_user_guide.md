# Administrator User Guide

**Skill Resume Certificate Verification System**

---

## 1. Overview & Administrator Responsibilities

The **Administrator** role provides full platform governance, security compliance, candidate verification, and reporting capabilities. Administrators are responsible for:
1. Reviewing pending candidate certificates in a human-in-the-loop workflow.
2. Authenticating genuine credentials and rejecting fraudulent or malformed submissions.
3. Managing user accounts, auditing activity, and activating/deactivating accounts.
4. Exporting compliance reports and audit logs for institutional evaluation.

---

## 2. Accessing the Administrator Portal

1. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/auth/login
   ```
2. Log in using your administrator credentials:
   * **Email / Username**: `admin@skillverify.com` (or `admin`)
   * **Password**: `admin123`
3. Upon successful authentication, you will be redirected to the **Admin Dashboard** (`/admin/dashboard`).

---

## 3. Navigating the Admin Dashboard

The Admin Dashboard provides real-time visibility into platform health:
* **Metric Cards**:
  * **Total Registered Users**: Total accounts registered in the database.
  * **Job Seekers**: Total candidate accounts.
  * **Total Resumes**: Number of digital and uploaded resumes.
  * **Total Certificates**: Total credentials submitted.
  * **Pending Verification Queue**: Submissions awaiting administrator review (with direct shortcut).
  * **Verified Certificates**: Credentials approved by administrators.
  * **Rejected Certificates**: Submissions rejected due to invalidity or expired status.
* **Graphical Visualizations**:
  * **Verification Breakdown**: Interactive Chart.js doughnut chart depicting verified vs. pending vs. rejected percentages.
* **Quick Action Controls**:
  * Jump directly to the **Pending Queue**.
  * Access **User Management**.
  * View **Audit History**.
  * Generate **Reports & Analytics**.

---

## 4. Certificate Verification Workflow

### 4.1 Accessing the Pending Queue
Click **Verification Queue** in the top navigation bar or navigate to:
```
http://127.0.0.1:5000/verification/queue
```

### 4.2 Inspecting Certificate Submissions
For each certificate in the queue:
1. Examine candidate name, certificate title, issuing organization, issue date, and expiration date.
2. Click **View Document** to securely inspect the uploaded PDF or image file directly in the browser.
3. If an external credential URL or credential ID is provided, verify it against the issuing body.

### 4.3 Approving or Rejecting a Certificate
1. Enter mandatory or optional **Reviewer Remarks** in the input field (e.g., *"Verified via CNCF public credential registry"* or *"Document illegible / Missing official seal"*).
2. Click **Verify (Approve)** to authenticate the certificate:
   * Status changes to `verified`.
   * The candidate receives a real-time notification.
   * An immutable `VerificationRecord` is recorded with your administrator ID and timestamp.
3. Click **Reject** to decline the certificate:
   * Status changes to `rejected`.
   * Candidate receives notification with your specific remarks.

---

## 5. User Account Management

Navigate to **User Management** via the navigation bar (`/admin/users`):
* **Search & Filter**:
  * Search by username, full name, or email address.
  * Filter by Role (`Job Seeker`, `Administrator`).
  * Filter by Status (`Active`, `Inactive`).
* **Inspecting Candidate Details**:
  * Click **View Profile** to review candidate bio, education history, skills, resumes, and certificates.
* **Toggling Account Status**:
  * Click **Deactivate** to suspend a user account. Deactivated users cannot log into the platform.
  * Click **Activate** to restore an account's active standing.

---

## 6. Verification Audit History

Navigate to **Verification History** (`/admin/verifications`):
* View the complete, immutable historical audit trail of all administrative decisions.
* Filter by decision type: **All Actions**, **Verified Only**, or **Rejected Only**.
* Review timestamps, administrator identity, and specific justification remarks.

---

## 7. Reports and Analytics

Navigate to **Reports & Analytics** (`/reports/`):
* **Date Range Filtering**: Specify custom Start Date and End Date filters to analyze submissions during specific academic terms or recruitment cycles.
* **Key Metrics**: View verified rates, rejection rates, pending queue volume, and submission trends.
* **Longitudinal Trends**: Grouped bar chart depicting 6-month registration and submission activity.
* **Download Executive PDF Report**: Click **Download PDF Report** to generate a formatted compliance document using the ReportLab engine.
* **Export CSV Data**: Click **Export Audit CSV** to download a spreadsheet of all decisions and candidate submissions.
