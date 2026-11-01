import urllib.request
import urllib.parse
import http.cookiejar
import re

def run_live_test():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # 1. Fetch register page
    print("1. Checking registration page...")
    resp = opener.open('http://127.0.0.1:5000/auth/register')
    html = resp.read().decode('utf-8')
    assert 'Select Account Role' not in html, "Role selection must be removed"
    assert 'id="role_admin"' not in html, "Admin radio option must be removed"
    assert 'Job Seeker Account Registration' in html, "Job Seeker notice should be present"

    token_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert token_match, "CSRF token missing from register page"
    csrf_token = token_match.group(1)
    print("   [OK] Registration page verified: Admin option removed, Job Seeker role enforced, CSRF token present")

    # 2. Register new Job Seeker
    print("2. Testing public Job Seeker registration...")
    reg_payload = urllib.parse.urlencode({
        'csrf_token': csrf_token,
        'first_name': 'Sarah',
        'last_name': 'Connor',
        'username': 'sarah_seeker',
        'email': 'sarah_seeker@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }).encode('utf-8')

    req_reg = urllib.request.Request('http://127.0.0.1:5000/auth/register', data=reg_payload)
    resp_reg = opener.open(req_reg)
    html_reg = resp_reg.read().decode('utf-8')
    assert 'Registration successful' in html_reg, "Registration banner not displayed"
    print("   [OK] Registration succeeded and redirected to login")

    # 3. Log in as Sarah
    print("3. Logging in as Job Seeker...")
    token_match_login = re.search(r'name="csrf_token" value="([^"]+)"', html_reg)
    csrf_login = token_match_login.group(1) if token_match_login else csrf_token

    login_payload = urllib.parse.urlencode({
        'csrf_token': csrf_login,
        'login_identifier': 'sarah_seeker',
        'password': 'Password123!'
    }).encode('utf-8')

    req_login = urllib.request.Request('http://127.0.0.1:5000/auth/login', data=login_payload)
    resp_logged = opener.open(req_login)
    html_dash = resp_logged.read().decode('utf-8')
    assert 'Sarah Connor' in html_dash, "Dashboard should display Sarah Connor"
    assert 'Upload Certificate' in html_dash, "Upload Certificate section must be present on dashboard"
    assert 'My Certificates' in html_dash, "My Certificates table must be present on dashboard"
    print("   [OK] Dashboard loaded with Certificate Upload section and My Certificates table")

    # 4. Upload Certificate with multipart/form-data
    print("4. Testing certificate upload on live server...")
    token_match_dash = re.search(r'name="csrf_token" value="([^"]+)"', html_dash)
    csrf_dash = token_match_dash.group(1)

    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="csrf_token"\r\n\r\n{csrf_dash}\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="title"\r\n\r\nGoogle Cloud Certified DevOps Engineer\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="issuing_organization"\r\n\r\nGoogle Cloud\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="issue_date"\r\n\r\n2026-05-20\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="credential_id"\r\n\r\nGCP-DEV-2026-99\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="certificate_file"; filename="gcp_cert.pdf"\r\n'
        f'Content-Type: application/pdf\r\n\r\n'
        f'%PDF-1.4 Mock live certificate document content\r\n'
        f'--{boundary}--\r\n'
    ).encode('utf-8')

    req_upload = urllib.request.Request('http://127.0.0.1:5000/seeker/upload-certificate', data=body)
    req_upload.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

    resp_uploaded = opener.open(req_upload)
    html_after_upload = resp_uploaded.read().decode('utf-8')
    assert 'Certificate uploaded successfully' in html_after_upload, "Upload confirmation flash message missing"
    assert 'Google Cloud Certified DevOps Engineer' in html_after_upload, "Uploaded certificate title missing from dashboard"
    assert 'Google Cloud' in html_after_upload, "Issuing organization missing from dashboard"
    assert 'Pending' in html_after_upload, "Status badge should display Pending"
    assert 'GCP-DEV-2026-99' in html_after_upload, "Credential ID missing from dashboard"
    print("   [OK] Certificate uploaded successfully; verified status is 'Pending' on Job Seeker dashboard")

    print("\n[SUCCESS] All live server tests executed and passed!")

if __name__ == '__main__':
    run_live_test()
