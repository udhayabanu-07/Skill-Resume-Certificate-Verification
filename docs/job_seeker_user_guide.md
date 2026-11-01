# Job Seeker User Guide

**Skill Resume Certificate Verification System**

---

## 1. Candidate Getting Started

Welcome to the **Skill Resume Certificate Verification System**! As a Job Seeker, this platform enables you to build a verifiable digital portfolio, create multi-template PDF resumes, upload academic and industry certificates, and obtain trusted administrator verification badges.

---

## 2. Account Registration and Sign In

### 2.1 Public Registration
1. Navigate to: `http://127.0.0.1:5000/auth/register`
2. Fill in:
   * **First Name & Last Name**
   * **Desired Username**
   * **Email Address**
   * **Password & Password Confirmation** (minimum 8 characters with at least one number and special character)
3. Submit the registration form. Public registration automatically provisions a **Job Seeker** account.

### 2.2 Logging In
1. Navigate to: `http://127.0.0.1:5000/auth/login`
2. Enter your username or email address and password.
3. Click **Sign In** to access your **Job Seeker Portal Dashboard**.

---

## 3. Profile Management & Completion Score

### 3.1 Viewing and Editing Your Profile
* Click **My Profile** in the top navigation or user menu (`/seeker/profile`).
* Click **Edit Profile** (`/seeker/profile/edit`) to manage:
  * **Contact Details**: Phone number, residential address, city, state, country.
  * **Date of Birth**: Used for identity verification.
  * **Professional Photograph**: Upload avatar image (JPG, PNG). The system automatically crops and verifies your photo using Pillow.
  * **Career Objective / Bio**: A summary of your professional goals.
  * **Social & Portfolio Links**: LinkedIn URL, GitHub profile, and personal website.

### 3.2 Dynamic Profile Completion Indicator
The system computes your **Profile Strength** dynamically:
* Adding your full name and contact information increases your score.
* Adding education entries and skills adds critical percentages.
* Uploading an avatar photo and linking social profiles reaches 100% completion.

---

## 4. Resume Management

### 4.1 Interactive Resume Builder
Navigate to **Resume Builder** (`/seeker/resume/builder`):
* **Education**: Add degrees, universities, graduation years, GPA, and honors.
* **Work Experience**: Add previous employers, job titles, tenures, and responsibilities.
* **Skills**:
  * Categorize skills as **Technical Skills** (e.g., Python, Docker, SQL) or **Soft Skills** (e.g., Leadership, Agile, Communication).
  * Rate your proficiency from *Beginner* to *Expert*.
  * **Link with Certificate**: Associate your skill directly with an uploaded certificate to showcase verified competency.
* **Projects & Achievements**: Add key software projects, hackathons, and certifications.

### 4.2 Multi-Template PDF Generation
Navigate to **Resume Preview** (`/seeker/resume/preview`):
* Review your formatted resume online.
* Use the **Template Selector** dropdown to choose your visual style:
  1. **Modern**: Features teal accents, centered header, and structured dividers.
  2. **Executive**: Features navy corporate branding, bold typography, and left-aligned executive headers.
  3. **Minimal**: Features clean monochrome formatting ideal for ATS parsing and technical CVs.
* Click **Download PDF Resume** to download your ReportLab-generated high-resolution document.

### 4.3 Uploading an Existing Resume
If you already have a resume prepared in PDF or DOCX format:
* Use the **Upload Existing Resume** card on your dashboard.
* Select your file (up to 16 MB) and click **Upload Resume**.

---

## 5. Certificate Submission & Verification

### 5.1 Uploading a Certificate
1. On your **Job Seeker Dashboard** (`/seeker/dashboard`), scroll to the **Upload Certificate** section.
2. Complete the required credential fields:
   * **Certificate Title** (e.g., *AWS Certified Solutions Architect*)
   * **Issuing Organization** (e.g., *Amazon Web Services*)
   * **Issue Date & Expiration Date** (optional expiration date for renewable credentials)
   * **Credential ID / License Number** (optional reference identifier)
   * **Certificate Document**: Upload the digital proof in **PDF, JPG, JPEG, or PNG** format.
3. Click **Submit for Verification**.

### 5.2 Understanding Verification Statuses
* <span style="color: #D97706; font-weight: bold;">PENDING</span>: Your certificate has been securely uploaded and queued for human administrator review.
* <span style="color: #059669; font-weight: bold;">VERIFIED</span>: An administrator has reviewed your document and verified its authenticity. A verified badge will appear on your resume and candidate profile.
* <span style="color: #DC2626; font-weight: bold;">REJECTED</span>: The certificate could not be authenticated. You can view the administrator's review remarks to understand the reason (e.g., missing seal, illegible text).

### 5.3 Editing and Deleting Certificates
* You can update metadata (such as credential IDs or expiration dates) by clicking **Edit** next to any certificate.
* You can safely remove certificates using the **Delete** button.

---

## 6. Notifications and Directory Discovery

### 6.1 In-App Notifications
* The **Bell Icon** in the top navigation bar displays your unread notification count.
* When an administrator reviews your certificate, you receive an instant notification containing the decision and reviewer remarks.
* Click **Mark as Read** to clear individual notices or **Mark All as Read** to clear your inbox.

### 6.2 Public Candidate Directory
* Candidates with complete profiles and verified credentials appear in the **Candidate Discovery Directory** (`/candidates`).
* Recruiters and peers can discover your profile by filtering for your verified skills, education, or degree.
