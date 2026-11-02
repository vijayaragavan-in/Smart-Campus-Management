# Smart Campus Management System

A diploma/undergraduate mini-project built with Python Flask and MySQL.

## Features
- Role-based login: admin, faculty, student
- Admin: create student accounts and publish announcements
- Faculty/admin: mark attendance for enrolled students
- Student: view course-wise attendance summary
- All roles: view announcements and timetable
- Server-side role checks, password hashing, parameterized SQL

## Requirements
- Python 3.10+
- MySQL Server 8.x (or compatible)
- A browser

## Setup (local development)

1. Create a virtual environment:
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
2. Install packages: `pip install -r requirements.txt`
3. Create the database and tables by running `schema.sql` in MySQL:
   `mysql -u root -p < schema.sql`
4. Create a restricted database user, for example:
   ```sql
   CREATE USER 'campus_app'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
   GRANT SELECT, INSERT, UPDATE, DELETE ON smart_campus.* TO 'campus_app'@'localhost';
   FLUSH PRIVILEGES;
   ```
5. Copy `.env.example` to `.env`, set the database credentials, and set a long random `FLASK_SECRET_KEY`.
6. Create the first admin account using the one-time script below.
7. Run: `flask --app app run --debug`
8. Open `http://127.0.0.1:5000`.

## Create first admin account

Run this from the project directory after setting up `.env` and the database:

```bash
python create_admin.py
```

The script asks for the admin name, email, and password and stores a password hash.

## Important: initial data
The starter app supports creating students and publishing notices, but course, faculty, enrollment, and timetable records must be inserted into MySQL (or you can extend the admin screens). Attendance requires a faculty record assigned to the course and student enrollments. See `sample_data.sql` for example setup records; edit the sample values before running it.

## Security notes
- This is an educational starter, not production-ready campus software.
- Add CSRF protection (e.g. Flask-WTF) before deployment.
- Use HTTPS and secure session cookie settings in production.
- Never use Flask debug mode on a public server.
- Use test data only until access control, backups, and institutional privacy requirements are reviewed.

## Create a faculty account

After configuring `.env`, run `python create_faculty.py`. Then insert a course assigned to the new faculty ID and enroll students for attendance testing.
