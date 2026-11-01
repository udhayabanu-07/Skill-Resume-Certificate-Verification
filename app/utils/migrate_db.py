import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'instance', 'skill_verify.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    def get_columns(table):
        c.execute(f"PRAGMA table_info({table})")
        return [col[1] for col in c.fetchall()]

    jsp_cols = get_columns('job_seeker_profiles')
    if 'date_of_birth' not in jsp_cols:
        c.execute("ALTER TABLE job_seeker_profiles ADD COLUMN date_of_birth DATE")
        print("Added date_of_birth to job_seeker_profiles")
    if 'state' not in jsp_cols:
        c.execute("ALTER TABLE job_seeker_profiles ADD COLUMN state VARCHAR(64)")
        print("Added state to job_seeker_profiles")

    skill_cols = get_columns('skills')
    if 'category' not in skill_cols:
        c.execute("ALTER TABLE skills ADD COLUMN category VARCHAR(20) DEFAULT 'technical'")
        print("Added category to skills")
    if 'certificate_id' not in skill_cols:
        c.execute("ALTER TABLE skills ADD COLUMN certificate_id INTEGER REFERENCES certificates(id) ON DELETE SET NULL")
        print("Added certificate_id to skills")

    cert_cols = get_columns('certificates')
    if 'expiration_date' not in cert_cols:
        c.execute("ALTER TABLE certificates ADD COLUMN expiration_date DATE")
        print("Added expiration_date to certificates")

    conn.commit()
    conn.close()
    print("Database schema migration completed successfully.")

if __name__ == '__main__':
    migrate()
