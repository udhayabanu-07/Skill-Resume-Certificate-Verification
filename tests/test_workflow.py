import os
import io
import unittest
from datetime import date
from flask import session
from app import create_app
from app.extensions import db
from app.models import (
    User,
    JobSeekerProfile,
    Education,
    Skill,
    WorkExperience,
    Project,
    Achievement,
    Resume,
    Certificate,
    VerificationRecord,
    Notification
)


class WorkflowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_csrf_token(self):
        """Helper to set and return a valid CSRF token in test client session."""
        token = 'mock-test-csrf-token-12345678'
        with self.client.session_transaction() as sess:
            sess['_csrf_token'] = token
        return token

    def test_registration_validation_and_job_seeker_role_enforcement(self):
        """Test public registration strictly creates Job Seeker accounts and rejects invalid input."""
        csrf = self.get_csrf_token()

        # 1. Missing first_name or last_name
        res = self.client.post('/auth/register', data={
            'csrf_token': csrf,
            'first_name': '',
            'last_name': '',
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=True)
        self.assertIn(b"First name is required", res.data)

        # 2. Short password or password mismatch
        res = self.client.post('/auth/register', data={
            'csrf_token': csrf,
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'short',
            'confirm_password': 'short'
        }, follow_redirects=True)
        self.assertIn(b"Password must be at least 8 characters long", res.data)

        # 3. Successful registration with malicious 'role=admin' attempted
        res = self.client.post('/auth/register', data={
            'csrf_token': csrf,
            'first_name': 'Alice',
            'last_name': 'Smith',
            'username': 'alice_seeker',
            'email': 'alice@example.com',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
            'role': 'admin'  # Attacker tries to register as admin
        }, follow_redirects=True)
        self.assertIn(b"Registration successful", res.data)

        # Verify user in database is strictly a job_seeker
        user = User.query.filter_by(username='alice_seeker').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, 'job_seeker')
        self.assertTrue(user.is_job_seeker)
        self.assertFalse(user.is_admin)

        # Verify profile was automatically created
        profile = JobSeekerProfile.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.first_name, 'Alice')
        self.assertEqual(profile.last_name, 'Smith')
        self.assertEqual(profile.full_name, 'Alice Smith')

        # 4. Duplicate username or email
        res_dup = self.client.post('/auth/register', data={
            'csrf_token': csrf,
            'first_name': 'Alice',
            'last_name': 'Duplicate',
            'username': 'alice_seeker',
            'email': 'different@example.com',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!'
        }, follow_redirects=True)
        self.assertIn(b"username is already taken", res_dup.data)

    def test_certificate_upload_and_status(self):
        """Test authenticated job seeker certificate upload, validation, and pending status."""
        # Create seeker user
        seeker = User(username='bob_seeker', email='bob@example.com', role='job_seeker')
        seeker.set_password('Password123!')
        db.session.add(seeker)
        db.session.flush()

        profile = JobSeekerProfile(user_id=seeker.id, first_name='Bob', last_name='Builder')
        db.session.add(profile)
        db.session.commit()

        # Login as bob
        csrf = self.get_csrf_token()
        login_res = self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'login_identifier': 'bob_seeker',
            'password': 'Password123!'
        }, follow_redirects=True)
        self.assertIn(b"Welcome back, bob_seeker", login_res.data)

        # 1. Test uploading invalid file format (.txt)
        csrf = self.get_csrf_token()
        fake_txt = (io.BytesIO(b"Hello text file content"), 'test.txt')
        res_invalid = self.client.post('/seeker/upload-certificate', data={
            'csrf_token': csrf,
            'title': 'Python Expert',
            'issuing_organization': 'Python Org',
            'issue_date': '2026-05-10',
            'certificate_file': fake_txt
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b"Only PDF, JPG, and PNG files are allowed", res_invalid.data)

        # 2. Test uploading valid PDF file
        csrf = self.get_csrf_token()
        valid_pdf = (io.BytesIO(b"%PDF-1.4 mock pdf data content"), 'my_cert.pdf')
        res_valid = self.client.post('/seeker/upload-certificate', data={
            'csrf_token': csrf,
            'title': 'Certified Security Specialist',
            'issuing_organization': 'CyberSec Institute',
            'issue_date': '2026-04-15',
            'credential_id': 'SEC-2026-001',
            'certificate_file': valid_pdf
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b"Certificate uploaded successfully", res_valid.data)

        # Verify certificate saved in database with status 'pending'
        cert = Certificate.query.filter_by(title='Certified Security Specialist').first()
        self.assertIsNotNone(cert)
        self.assertEqual(cert.status, 'pending')
        self.assertEqual(cert.issuing_organization, 'CyberSec Institute')
        self.assertEqual(cert.credential_id, 'SEC-2026-001')
        self.assertEqual(cert.issue_date, date(2026, 4, 15))
        self.assertTrue(os.path.exists(cert.file_path))

        # Check that dashboard shows the uploaded certificate and status 'pending'
        res_dash = self.client.get('/seeker/dashboard')
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn(b"Certified Security Specialist", res_dash.data)
        self.assertIn(b"CyberSec Institute", res_dash.data)
        self.assertIn(b"Pending", res_dash.data)

        # 3. Test uploading empty file (0 bytes)
        csrf = self.get_csrf_token()
        empty_file = (io.BytesIO(b""), 'empty.pdf')
        res_empty = self.client.post('/seeker/upload-certificate', data={
            'csrf_token': csrf,
            'title': 'Empty Cert',
            'issuing_organization': 'Empty Org',
            'certificate_file': empty_file
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b"file is empty", res_empty.data)

        # 4. Test missing certificate title and organization
        csrf = self.get_csrf_token()
        valid_pdf2 = (io.BytesIO(b"%PDF-1.4 test"), 'valid.pdf')
        res_missing = self.client.post('/seeker/upload-certificate', data={
            'csrf_token': csrf,
            'title': '',
            'issuing_organization': '',
            'certificate_file': valid_pdf2
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b"Certificate Name / Title is required", res_missing.data)
        self.assertIn(b"Issuing Organization is required", res_missing.data)

        # 5. Test uploading valid PNG file
        csrf = self.get_csrf_token()
        valid_png = (io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR mock png data"), 'aws_cert.png')
        res_png = self.client.post('/seeker/upload-certificate', data={
            'csrf_token': csrf,
            'title': 'AWS Solutions Architect',
            'issuing_organization': 'Amazon Web Services',
            'issue_date': '2026-01-20',
            'certificate_file': valid_png
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b"Certificate uploaded successfully", res_png.data)

        cert_png = Certificate.query.filter_by(title='AWS Solutions Architect').first()
        self.assertIsNotNone(cert_png)
        self.assertEqual(cert_png.status, 'pending')

        # 6. Test viewing certificate document
        res_view = self.client.get(f'/seeker/certificate/{cert_png.id}/view')
        self.assertEqual(res_view.status_code, 200)

    def test_security_access_controls_and_admin_review(self):
        """Test role access controls and authorized admin certificate review."""
        # Create Seeker and Admin users
        seeker = User(username='seeker_dan', email='dan@example.com', role='job_seeker')
        seeker.set_password('Password123!')
        db.session.add(seeker)
        db.session.flush()

        profile = JobSeekerProfile(user_id=seeker.id, first_name='Dan', last_name='Ray')
        db.session.add(profile)
        db.session.flush()

        admin = User(username='admin_boss', email='boss@example.com', role='admin')
        admin.set_password('AdminPass123!')
        db.session.add(admin)

        # Create a pending certificate for Dan
        cert = Certificate(
            profile_id=profile.id,
            title='Google Cloud Architect',
            issuing_organization='Google',
            issue_date=date(2026, 3, 1),
            original_filename='gcp.pdf',
            stored_filename='test_gcp.pdf',
            file_path='/tmp/test_gcp.pdf',
            file_size=1024,
            mime_type='application/pdf',
            status='pending'
        )
        db.session.add(cert)
        db.session.commit()

        # 1. Unauthenticated access to queue -> redirected to login
        res = self.client.get('/verification/queue')
        self.assertEqual(res.status_code, 302)

        # 2. Seeker attempts to access admin verification queue -> 403 Forbidden
        csrf = self.get_csrf_token()
        self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'login_identifier': 'seeker_dan',
            'password': 'Password123!'
        })
        res_forbidden = self.client.get('/verification/queue')
        self.assertEqual(res_forbidden.status_code, 403)

        # Seeker attempts to approve certificate -> 403 Forbidden
        csrf = self.get_csrf_token()
        res_illegal_approve = self.client.post(f'/verification/review/{cert.id}', data={
            'csrf_token': csrf,
            'action': 'verified'
        })
        self.assertEqual(res_illegal_approve.status_code, 403)

        # Verify cert remains pending
        cert_check = Certificate.query.get(cert.id)
        self.assertEqual(cert_check.status, 'pending')

        # Logout seeker
        self.client.get('/auth/logout')

        # 3. Admin logs in
        csrf = self.get_csrf_token()
        self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'login_identifier': 'admin_boss',
            'password': 'AdminPass123!'
        })

        # Admin views verification queue -> 200 OK
        res_queue = self.client.get('/verification/queue')
        self.assertEqual(res_queue.status_code, 200)
        self.assertIn(b"Google Cloud Architect", res_queue.data)

        # Admin approves certificate
        csrf = self.get_csrf_token()
        res_approve = self.client.post(f'/verification/review/{cert.id}', data={
            'csrf_token': csrf,
            'action': 'verified',
            'remarks': 'Official credential ID verified with Google directory.'
        }, follow_redirects=True)
        self.assertEqual(res_approve.status_code, 200)

        # Verify certificate in database is verified
        cert_after = Certificate.query.get(cert.id)
        self.assertEqual(cert_after.status, 'verified')
        self.assertEqual(cert_after.verified_by_id, admin.id)

        # Verify audit record was created
        record = VerificationRecord.query.filter_by(certificate_id=cert.id).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.action, 'verified')
        self.assertEqual(record.admin_id, admin.id)
        self.assertIn('Official credential ID verified', record.remarks)

    def test_resume_management_workflow(self):
        """Test complete resume lifecycle: personal info, objective, education, skills, experience, projects, achievements, preview, PDF download, and upload."""
        # 1. Create Job Seeker
        seeker = User(username='elena_dev', email='elena@example.com', role='job_seeker')
        seeker.set_password('Password123!')
        db.session.add(seeker)
        db.session.flush()

        profile = JobSeekerProfile(
            user_id=seeker.id,
            first_name='Elena',
            last_name='Rostova',
            headline='Cloud Backend Engineer',
            phone='+1 555 0199',
            city='Seattle',
            country='USA'
        )
        db.session.add(profile)
        db.session.commit()

        # Login as Elena
        csrf = self.get_csrf_token()
        self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'login_identifier': 'elena_dev',
            'password': 'Password123!'
        })

        # 2. Update Personal Info & Career Objective (Edit Resume)
        csrf = self.get_csrf_token()
        res_update = self.client.post('/seeker/resume/builder', data={
            'csrf_token': csrf,
            'first_name': 'Elena',
            'last_name': 'Rostova',
            'headline': 'Senior Cloud Backend Engineer',
            'phone': '+1 555 0199',
            'city': 'Seattle',
            'country': 'USA',
            'address': '700 Pike St',
            'linkedin_url': 'https://linkedin.com/in/elena-dev',
            'github_url': 'https://github.com/elena-dev',
            'portfolio_url': 'https://elena.codes',
            'career_objective': 'Passionate engineer dedicated to resilient distributed systems and secure cloud backends.'
        }, follow_redirects=True)
        self.assertIn(b"Resume details updated successfully", res_update.data)

        # Verify profile updated in DB
        db.session.refresh(profile)
        self.assertEqual(profile.headline, 'Senior Cloud Backend Engineer')
        self.assertEqual(profile.effective_objective, 'Passionate engineer dedicated to resilient distributed systems and secure cloud backends.')
        self.assertEqual(profile.portfolio_url, 'https://elena.codes')

        # 3. Add Education
        csrf = self.get_csrf_token()
        res_edu = self.client.post('/seeker/resume/education/add', data={
            'csrf_token': csrf,
            'institution': 'University of Washington',
            'degree': 'Master of Science',
            'field_of_study': 'Computer Science',
            'start_date': '2020-09-01',
            'end_date': '2022-06-15',
            'grade_or_cgpa': '3.95 / 4.0',
            'description': 'Thesis on distributed consensus algorithms.'
        }, follow_redirects=True)
        self.assertIn(b"Education entry added successfully", res_edu.data)
        self.assertEqual(profile.education_entries.count(), 1)

        # 4. Add Skills
        csrf = self.get_csrf_token()
        self.client.post('/seeker/resume/skill/add', data={
            'csrf_token': csrf,
            'name': 'Python',
            'proficiency_level': 'expert',
            'years_of_experience': '5.0'
        }, follow_redirects=True)
        self.client.post('/seeker/resume/skill/add', data={
            'csrf_token': csrf,
            'name': 'Docker',
            'proficiency_level': 'advanced',
            'years_of_experience': '4.0'
        }, follow_redirects=True)
        self.assertEqual(profile.skills.count(), 2)

        # 5. Add Work Experience
        csrf = self.get_csrf_token()
        res_exp = self.client.post('/seeker/resume/experience/add', data={
            'csrf_token': csrf,
            'company': 'Tech Solutions Inc',
            'job_title': 'Senior Backend Engineer',
            'location': 'Seattle, WA',
            'start_date': '2022-07-01',
            'is_current': 'true',
            'description': 'Architected high-throughput microservices using Python, Flask, and PostgreSQL.'
        }, follow_redirects=True)
        self.assertIn(b"Work experience added successfully", res_exp.data)
        self.assertEqual(profile.work_experiences.count(), 1)

        # 6. Add Project
        csrf = self.get_csrf_token()
        res_proj = self.client.post('/seeker/resume/project/add', data={
            'csrf_token': csrf,
            'title': 'Distributed Credential Vault',
            'technologies': 'Python, Cryptography, Docker',
            'project_url': 'https://github.com/elena-dev/vault',
            'description': 'Encrypted credential vault with role-based audit logs.'
        }, follow_redirects=True)
        self.assertIn(b"Distributed Credential Vault", res_proj.data)
        self.assertIn(b"added successfully", res_proj.data)
        self.assertEqual(profile.projects.count(), 1)

        # 7. Add Achievement
        csrf = self.get_csrf_token()
        res_ach = self.client.post('/seeker/resume/achievement/add', data={
            'csrf_token': csrf,
            'title': 'Best Cloud Architecture Award 2025',
            'date_achieved': '2025-11-10',
            'description': 'Awarded for zero-downtime database migration architecture.'
        }, follow_redirects=True)
        self.assertIn(b"Best Cloud Architecture Award 2025", res_ach.data)
        self.assertIn(b"added successfully", res_ach.data)
        self.assertEqual(profile.achievements.count(), 1)

        # 8. Test Resume Web Preview (View Resume)
        res_preview = self.client.get('/seeker/resume/preview')
        self.assertEqual(res_preview.status_code, 200)
        self.assertIn(b"Elena Rostova", res_preview.data)
        self.assertIn(b"Senior Cloud Backend Engineer", res_preview.data)
        self.assertIn(b"Passionate engineer dedicated to resilient distributed systems", res_preview.data)
        self.assertIn(b"University of Washington", res_preview.data)
        self.assertIn(b"Python", res_preview.data)
        self.assertIn(b"Tech Solutions Inc", res_preview.data)
        self.assertIn(b"Distributed Credential Vault", res_preview.data)
        self.assertIn(b"Best Cloud Architecture Award 2025", res_preview.data)

        # 9. Test Resume PDF Download (ReportLab)
        res_pdf = self.client.get('/seeker/resume/download-pdf')
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf.content_type, 'application/pdf')
        self.assertTrue(res_pdf.data.startswith(b'%PDF-'))
        self.assertGreater(len(res_pdf.data), 1000)

        # 10. Test Uploading Existing Resume (PDF and DOCX)
        csrf = self.get_csrf_token()
        # Invalid file upload (.exe)
        bad_file = (io.BytesIO(b"malicious executable"), 'virus.exe')
        res_bad = self.client.post('/seeker/resume/upload', data={
            'csrf_token': csrf,
            'resume_file': bad_file
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b"Only PDF and DOCX resume documents are allowed", res_bad.data)

        # Valid PDF upload
        csrf = self.get_csrf_token()
        valid_pdf = (io.BytesIO(b"%PDF-1.4 Mock resume document content"), 'Elena_Official_Resume.pdf')
        res_upload_pdf = self.client.post('/seeker/resume/upload', data={
            'csrf_token': csrf,
            'resume_file': valid_pdf
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b"Resume document uploaded successfully", res_upload_pdf.data)
        self.assertEqual(profile.resumes.count(), 1)
        uploaded_res = profile.resumes.first()
        self.assertTrue(uploaded_res.is_primary)

        # Valid DOCX upload
        csrf = self.get_csrf_token()
        valid_docx = (io.BytesIO(b"PK\x03\x04 mock word document data"), 'Elena_Resume.docx')
        res_upload_docx = self.client.post('/seeker/resume/upload', data={
            'csrf_token': csrf,
            'resume_file': valid_docx
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b"Resume document uploaded successfully", res_upload_docx.data)
        self.assertEqual(profile.resumes.count(), 2)

        # View uploaded resume file
        res_view_file = self.client.get(f'/seeker/resume/uploaded/{uploaded_res.id}/view')
        self.assertEqual(res_view_file.status_code, 200)

        # 11. Security Tests: Role & Ownership Restrictions
        # Create second seeker
        other_seeker = User(username='hacker_bob', email='bob_hacker@example.com', role='job_seeker')
        other_seeker.set_password('Password123!')
        db.session.add(other_seeker)
        db.session.flush()
        other_profile = JobSeekerProfile(user_id=other_seeker.id, first_name='Bob', last_name='Hacker')
        db.session.add(other_profile)
        db.session.commit()

        # Logout Elena
        self.client.get('/auth/logout')

        # Login as other seeker
        csrf = self.get_csrf_token()
        self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'login_identifier': 'hacker_bob',
            'password': 'Password123!'
        })

        # Other seeker cannot view Elena's uploaded resume -> 403 Forbidden
        res_unauth_view = self.client.get(f'/seeker/resume/uploaded/{uploaded_res.id}/view')
        self.assertEqual(res_unauth_view.status_code, 403)

        # Other seeker cannot delete Elena's uploaded resume -> 403 Forbidden
        csrf = self.get_csrf_token()
        res_unauth_del = self.client.post(f'/seeker/resume/uploaded/{uploaded_res.id}/delete', data={'csrf_token': csrf})
        self.assertEqual(res_unauth_del.status_code, 403)

        # Other seeker cannot access admin candidate resumes directory -> 403 Forbidden
        res_admin_dir = self.client.get('/admin/resumes')
        self.assertEqual(res_admin_dir.status_code, 403)

        # Logout Bob
        self.client.get('/auth/logout')

        # Admin logs in
        admin = User(username='chief_admin', email='chief@skillverify.com', role='admin')
        admin.set_password('AdminSecure123!')
        db.session.add(admin)
        db.session.commit()

        csrf = self.get_csrf_token()
        self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'login_identifier': 'chief_admin',
            'password': 'AdminSecure123!'
        })

        # Admin can access candidate resumes directory -> 200 OK
        res_admin_resumes = self.client.get('/admin/resumes')
        self.assertEqual(res_admin_resumes.status_code, 200)
        self.assertIn(b"Elena Rostova", res_admin_resumes.data)

        # Admin can view Elena's digital resume -> 200 OK
        res_admin_view_elena = self.client.get(f'/admin/seeker/{seeker.id}/resume')
        self.assertEqual(res_admin_view_elena.status_code, 200)
        self.assertIn(b"Elena Rostova", res_admin_view_elena.data)
        self.assertIn(b"Admin View Mode", res_admin_view_elena.data)

        # Admin can download Elena's resume PDF -> 200 OK
        res_admin_pdf_elena = self.client.get(f'/admin/seeker/{seeker.id}/resume/pdf')
        self.assertEqual(res_admin_pdf_elena.status_code, 200)
        self.assertTrue(res_admin_pdf_elena.data.startswith(b'%PDF-'))

    def test_profile_skills_and_certificate_lifecycle(self):
        """Test profile management, technical vs soft skills, certificate expiration, edit, delete, and multi-template PDF."""
        # 1. Register candidate
        seeker = User(username='carlos_dev', email='carlos@example.com', role='job_seeker')
        seeker.set_password('Password123!')
        db.session.add(seeker)
        db.session.flush()
        profile = JobSeekerProfile(user_id=seeker.id, first_name='Carlos', last_name='Mendez')
        db.session.add(profile)
        db.session.commit()

        # Login
        csrf = self.get_csrf_token()
        self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'login_identifier': 'carlos_dev',
            'password': 'Password123!'
        })

        # 2. Edit Profile
        csrf = self.get_csrf_token()
        res_edit_prof = self.client.post('/seeker/profile/edit', data={
            'csrf_token': csrf,
            'first_name': 'Carlos',
            'last_name': 'Mendez',
            'headline': 'Full Stack Cloud Architect',
            'phone': '+1 (555) 789-0123',
            'date_of_birth': '1995-04-12',
            'address': '742 Evergreen Terrace',
            'city': 'Springfield',
            'state': 'Oregon',
            'country': 'United States',
            'career_objective': 'Build scalable enterprise systems.',
            'bio': 'Over 8 years of engineering experience.',
            'linkedin_url': 'https://linkedin.com/in/carlosmendez',
            'github_url': 'https://github.com/carlosmendez',
            'portfolio_url': 'https://carlosmendez.dev'
        }, follow_redirects=True)
        self.assertEqual(res_edit_prof.status_code, 200)

        # 3. View Profile & verify completion percentage
        res_view_prof = self.client.get('/seeker/profile')
        self.assertEqual(res_view_prof.status_code, 200)
        self.assertIn(b"Carlos Mendez", res_view_prof.data)
        self.assertIn(b"Full Stack Cloud Architect", res_view_prof.data)
        self.assertGreater(profile.profile_completion_percentage, 40)

        # 4. Add Technical Skill
        csrf = self.get_csrf_token()
        self.client.post('/seeker/resume/skill/add', data={
            'csrf_token': csrf,
            'name': 'Kubernetes',
            'category': 'technical',
            'proficiency_level': 'expert',
            'years_of_experience': '4.5'
        })
        k8s_skill = Skill.query.filter_by(profile_id=profile.id, name='Kubernetes').first()
        self.assertIsNotNone(k8s_skill)
        self.assertEqual(k8s_skill.category, 'technical')

        # 5. Add Soft Skill
        csrf = self.get_csrf_token()
        self.client.post('/seeker/resume/skill/add', data={
            'csrf_token': csrf,
            'name': 'Team Leadership',
            'category': 'soft',
            'proficiency_level': 'advanced',
            'years_of_experience': '5.0'
        })
        soft_skill = Skill.query.filter_by(profile_id=profile.id, name='Team Leadership').first()
        self.assertIsNotNone(soft_skill)
        self.assertEqual(soft_skill.category, 'soft')

        # 6. Edit Skill
        csrf = self.get_csrf_token()
        self.client.post(f'/seeker/resume/skill/{k8s_skill.id}/edit', data={
            'csrf_token': csrf,
            'name': 'Kubernetes & Helm',
            'category': 'technical',
            'proficiency_level': 'expert',
            'years_of_experience': '5.0'
        })
        k8s_updated = Skill.query.filter_by(id=k8s_skill.id).first()
        self.assertEqual(k8s_updated.name, 'Kubernetes & Helm')

        # 7. Upload Certificate with Expiration Date
        cert_stream = io.BytesIO(b'%PDF-1.4 Mock CKA Certificate content')
        csrf = self.get_csrf_token()
        res_cert = self.client.post('/seeker/certificate/upload', data={
            'csrf_token': csrf,
            'title': 'Certified Kubernetes Administrator',
            'issuing_organization': 'Linux Foundation',
            'issue_date': '2023-01-15',
            'expiration_date': '2026-01-15',
            'credential_id': 'CKA-998877',
            'certificate_file': (cert_stream, 'cka_cert.pdf')
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res_cert.status_code, 200)

        cert = Certificate.query.filter_by(profile_id=profile.id, title='Certified Kubernetes Administrator').first()
        self.assertIsNotNone(cert)
        self.assertEqual(cert.expiration_date.strftime('%Y-%m-%d'), '2026-01-15')

        # 8. Edit Certificate Metadata
        csrf = self.get_csrf_token()
        res_edit_cert = self.client.post(f'/seeker/certificate/{cert.id}/edit', data={
            'csrf_token': csrf,
            'title': 'Certified Kubernetes Administrator (CKA)',
            'issuing_organization': 'CNCF / Linux Foundation',
            'issue_date': '2023-01-15',
            'expiration_date': '2026-01-15',
            'credential_id': 'CKA-998877-RENEWED'
        }, follow_redirects=True)
        self.assertEqual(res_edit_cert.status_code, 200)
        cert_after_edit = Certificate.query.filter_by(id=cert.id).first()
        self.assertEqual(cert_after_edit.title, 'Certified Kubernetes Administrator (CKA)')

        # 9. Test Multi-Template PDF Downloads
        for tpl in ['modern', 'executive', 'minimal']:
            res_pdf = self.client.get(f'/seeker/resume/download-pdf?template={tpl}')
            self.assertEqual(res_pdf.status_code, 200)
            self.assertTrue(res_pdf.data.startswith(b'%PDF-'))

        # 10. Delete Certificate
        csrf = self.get_csrf_token()
        res_del_cert = self.client.post(f'/seeker/certificate/{cert.id}/delete', data={'csrf_token': csrf}, follow_redirects=True)
        self.assertEqual(res_del_cert.status_code, 200)
        self.assertIsNone(Certificate.query.filter_by(id=cert.id).first())

    def test_admin_user_management_reports_and_candidates_directory(self):
        """Test candidate directory, notifications, password workflows, admin user management, and report analytics."""
        # 1. Setup Seeker and Admin
        seeker = User(username='maya_analyst', email='maya@example.com', role='job_seeker')
        seeker.set_password('Password123!')
        db.session.add(seeker)
        db.session.flush()
        profile = JobSeekerProfile(user_id=seeker.id, first_name='Maya', last_name='Patel', headline='Lead Data Analyst')
        db.session.add(profile)

        admin = User(username='super_admin', email='super_admin@skillverify.com', role='admin')
        admin.set_password('AdminMaster123!')
        db.session.add(admin)
        db.session.commit()

        # Add education and skill for directory filter test
        edu = Education(profile_id=profile.id, institution='MIT', degree='Master of Science', field_of_study='Data Science')
        skill = Skill(profile_id=profile.id, name='Data Modeling', category='technical')
        db.session.add_all([edu, skill])
        db.session.commit()

        # 2. Test Candidates Directory (Public Discovery)
        res_dir = self.client.get('/candidates')
        self.assertEqual(res_dir.status_code, 200)
        self.assertIn(b"Maya Patel", res_dir.data)

        # Search by keyword
        res_search = self.client.get('/candidates?search=Maya')
        self.assertEqual(res_search.status_code, 200)
        self.assertIn(b"Maya Patel", res_search.data)

        # Filter by skill
        res_skill_filter = self.client.get('/candidates?skill=Data+Modeling')
        self.assertEqual(res_skill_filter.status_code, 200)
        self.assertIn(b"Maya Patel", res_skill_filter.data)

        # Candidate public profile
        res_public_prof = self.client.get(f'/candidates/{profile.id}')
        self.assertEqual(res_public_prof.status_code, 200)
        self.assertIn(b"Lead Data Analyst", res_public_prof.data)
        self.assertIn(b"Master of Science", res_public_prof.data)

        # 3. Test Seeker Notifications
        csrf = self.get_csrf_token()
        self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'login_identifier': 'maya_analyst',
            'password': 'Password123!'
        })

        notif = Notification(user_id=seeker.id, title="Test Notification", message="Testing notification center.", is_read=False)
        db.session.add(notif)
        db.session.commit()

        res_notif_list = self.client.get('/seeker/notifications')
        self.assertEqual(res_notif_list.status_code, 200)
        self.assertIn(b"Test Notification", res_notif_list.data)

        csrf = self.get_csrf_token()
        self.client.post(f'/seeker/notifications/{notif.id}/mark-read', data={'csrf_token': csrf})
        notif_after = Notification.query.filter_by(id=notif.id).first()
        self.assertTrue(notif_after.is_read)

        # 4. Test Password Change
        csrf = self.get_csrf_token()
        res_change_pwd = self.client.post('/auth/change-password', data={
            'csrf_token': csrf,
            'current_password': 'Password123!',
            'new_password': 'BrandNewPassword456!',
            'confirm_password': 'BrandNewPassword456!'
        }, follow_redirects=True)
        self.assertEqual(res_change_pwd.status_code, 200)

        # Logout seeker
        self.client.get('/auth/logout')

        # Verify login with new password
        csrf = self.get_csrf_token()
        res_login_new = self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'login_identifier': 'maya_analyst',
            'password': 'BrandNewPassword456!'
        })
        self.assertEqual(res_login_new.status_code, 302)

        self.client.get('/auth/logout')

        # 5. Test Forgot Password Workflow
        csrf = self.get_csrf_token()
        res_forgot = self.client.post('/auth/forgot-password', data={
            'csrf_token': csrf,
            'identifier': 'maya@example.com'
        })
        self.assertEqual(res_forgot.status_code, 200)
        self.assertIn(b"reset-password", res_forgot.data)

        # 6. Admin Workflows
        csrf = self.get_csrf_token()
        self.client.post('/auth/login', data={
            'csrf_token': csrf,
            'login_identifier': 'super_admin',
            'password': 'AdminMaster123!'
        })

        # Admin Dashboard
        res_admin_dash = self.client.get('/admin/dashboard')
        self.assertEqual(res_admin_dash.status_code, 200)

        # Admin Users Directory
        res_users = self.client.get('/admin/users')
        self.assertEqual(res_users.status_code, 200)
        self.assertIn(b"maya_analyst", res_users.data)

        # Admin User Detail
        res_user_det = self.client.get(f'/admin/users/{seeker.id}')
        self.assertEqual(res_user_det.status_code, 200)
        self.assertIn(b"Maya Patel", res_user_det.data)

        # Admin Toggle User Status (Deactivate / Activate)
        csrf = self.get_csrf_token()
        self.client.post(f'/admin/users/{seeker.id}/toggle-status', data={'csrf_token': csrf})
        seeker_check = User.query.filter_by(id=seeker.id).first()
        self.assertFalse(seeker_check.is_active)

        csrf = self.get_csrf_token()
        self.client.post(f'/admin/users/{seeker.id}/toggle-status', data={'csrf_token': csrf})
        seeker_check_2 = User.query.filter_by(id=seeker.id).first()
        self.assertTrue(seeker_check_2.is_active)

        # Admin Reports & Analytics
        res_reports = self.client.get('/reports/')
        self.assertEqual(res_reports.status_code, 200)
        self.assertIn(b"Reports & Analytics", res_reports.data)

        # Reports CSV Export
        res_csv = self.client.get('/reports/export-csv')
        self.assertEqual(res_csv.status_code, 200)
        self.assertIn(b"Certificate ID", res_csv.data)

        # Reports PDF Generation
        res_rep_pdf = self.client.get('/reports/pdf')
        self.assertEqual(res_rep_pdf.status_code, 200)
        self.assertTrue(res_rep_pdf.data.startswith(b'%PDF-'))

        # Admin Verification Audit History
        res_ver_hist = self.client.get('/admin/verifications')
        self.assertEqual(res_ver_hist.status_code, 200)


if __name__ == '__main__':
    unittest.main()
