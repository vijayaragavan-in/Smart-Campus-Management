
import os
from functools import wraps
from datetime import date
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, abort, send_from_directory
)
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

load_dotenv(override=True)

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "FLASK_SECRET_KEY", "dev-only-change-me"
)

app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

UPLOAD_DIR = (
    Path(app.root_path)
    / "static"
    / "uploads"
    / "course_materials"
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MATERIAL_EXTENSIONS = {
    "pdf", "doc", "docx", "ppt", "pptx",
    "txt", "png", "jpg", "jpeg"
}


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "smart_campus")
    )


def query_all(sql, params=()):
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def query_one(sql, params=()):
    rows = query_all(sql, params)
    return rows[0] if rows else None


def execute_query(sql, params=()):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        cur.close()
        conn.close()


# --------------------------------------------------
# LOGIN AND ROLE DECORATORS
# --------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    def decorator(view):

        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):

            if session.get("role") not in roles:
                abort(403)

            return view(*args, **kwargs)

        return wrapped

    return decorator


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def index():

    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get("password", "")

        user = query_one(
            """
            SELECT id, name, email, password_hash, role
            FROM users
            WHERE email=%s
            """,
            (email,)
        )

        if user and check_password_hash(
            user["password_hash"], password
        ):

            session.clear()

            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))



# --------------------------------------------------
# RESET SESSION
# --------------------------------------------------

@app.route("/reset-session")
def reset_session():

    session.clear()

    return redirect(url_for("login"))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    role = session["role"]

    stats = {}
    low_attendance_alerts = []

    notices = query_all(
        """
        SELECT
            a.title,
            a.message,
            a.created_at,
            u.name AS author
        FROM announcements a
        JOIN users u ON u.id=a.created_by
        ORDER BY a.created_at DESC
        LIMIT 5
        """
    )

    # ADMIN DASHBOARD

    if role == "admin":

        stats = {
            "Students": query_one(
                "SELECT COUNT(*) AS n FROM students"
            )["n"],

            "Faculty": query_one(
                "SELECT COUNT(*) AS n FROM faculty"
            )["n"],

            "Courses": query_one(
                "SELECT COUNT(*) AS n FROM courses"
            )["n"],

            "Announcements": query_one(
                "SELECT COUNT(*) AS n FROM announcements"
            )["n"]
        }

    # STUDENT DASHBOARD

    elif role == "student":

        student = query_one(
            """
            SELECT id
            FROM students
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        if student:

            stats["Attendance records"] = query_one(
                """
                SELECT COUNT(*) AS n
                FROM attendance
                WHERE student_id=%s
                """,
                (student["id"],)
            )["n"]

            stats["Courses enrolled"] = query_one(
                """
                SELECT COUNT(*) AS n
                FROM enrollments
                WHERE student_id=%s
                """,
                (student["id"],)
            )["n"]

            # LOW ATTENDANCE WARNING SYSTEM

            low_attendance_alerts = query_all(
                """
                SELECT
                    c.course_code,
                    c.course_name,
                    COUNT(a.id) AS total_count,
                    SUM(a.status='present') AS present_count,
                    ROUND(
                        100 * SUM(a.status='present')
                        / NULLIF(COUNT(a.id), 0),
                        2
                    ) AS percentage

                FROM enrollments e

                JOIN courses c
                    ON c.id=e.course_id

                LEFT JOIN attendance a
                    ON a.course_id=c.id
                    AND a.student_id=e.student_id

                WHERE e.student_id=%s

                GROUP BY
                    c.id,
                    c.course_code,
                    c.course_name

                HAVING
                    COUNT(a.id)>0
                    AND percentage < 75

                ORDER BY percentage
                """,
                (student["id"],)
            )

        else:

            stats["Profile"] = "Not created"

    # FACULTY DASHBOARD

    elif role == "faculty":

        faculty = query_one(
            """
            SELECT id
            FROM faculty
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        stats["Assigned courses"] = (
            query_one(
                """
                SELECT COUNT(*) AS n
                FROM courses
                WHERE faculty_id=%s
                """,
                (faculty["id"],)
            )["n"]
            if faculty else 0
        )

    return render_template(
        "dashboard.html",
        stats=stats,
        notices=notices,
        low_attendance_alerts=low_attendance_alerts
    )


# --------------------------------------------------
# STUDENT RECORDS
# --------------------------------------------------

@app.route("/students")
@role_required("admin")
def students():

    rows = query_all(
        """
        SELECT
            s.id,
            u.name,
            u.email,
            s.roll_no,
            s.department,
            s.semester
        FROM students s
        JOIN users u ON u.id=s.user_id
        ORDER BY s.id DESC
        """
    )

    return render_template(
        "students.html",
        students=rows
    )


# --------------------------------------------------
# ATTENDANCE MANAGEMENT
# --------------------------------------------------

@app.route("/attendance", methods=["GET", "POST"])
@role_required("admin", "faculty")
def attendance():
    faculty_id = None

    # Faculty members can manage attendance only for their own courses.
    if session["role"] == "faculty":
        faculty = query_one(
            "SELECT id FROM faculty WHERE user_id=%s",
            (session["user_id"],)
        )
        if not faculty:
            abort(403)
        faculty_id = faculty["id"]

    # Load the courses available to this user.
    if faculty_id is not None:
        courses = query_all(
            """
            SELECT id, course_code, course_name
            FROM courses
            WHERE faculty_id=%s
            ORDER BY course_code
            """,
            (faculty_id,)
        )
    else:
        courses = query_all(
            """
            SELECT id, course_code, course_name
            FROM courses
            ORDER BY course_code
            """
        )

    if request.method == "POST":
        course_id = request.form.get("course_id", type=int)
        class_date = request.form.get("class_date") or date.today().isoformat()

        if not course_id:
            flash("Please select a course.", "error")
            return redirect(url_for("attendance"))

        # Verify faculty ownership before saving attendance.
        if faculty_id is not None:
            allowed = query_one(
                "SELECT id FROM courses WHERE id=%s AND faculty_id=%s",
                (course_id, faculty_id)
            )
            if not allowed:
                abort(403)

        enrolled_students = query_all(
            """
            SELECT s.id
            FROM enrollments e
            JOIN students s ON s.id=e.student_id
            WHERE e.course_id=%s
            ORDER BY s.roll_no
            """,
            (course_id,)
        )

        if not enrolled_students:
            flash("No students are enrolled in this course.", "error")
            return redirect(url_for(
                "attendance", course_id=course_id, class_date=class_date
            ))

        conn = get_db()
        cur = conn.cursor()
        try:
            for student in enrolled_students:
                status = request.form.get(
                    f"status_{student['id']}", "absent"
                )
                if status not in ("present", "absent"):
                    status = "absent"

                # Update an existing record for the same student/course/date;
                # otherwise insert a new attendance record.
                cur.execute(
                    """
                    SELECT id FROM attendance
                    WHERE student_id=%s AND course_id=%s AND class_date=%s
                    """,
                    (student["id"], course_id, class_date)
                )
                existing = cur.fetchone()

                if existing:
                    cur.execute(
                        """
                        UPDATE attendance
                        SET status=%s, marked_by=%s
                        WHERE id=%s
                        """,
                        (status, session["user_id"], existing[0])
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO attendance
                            (student_id, course_id, class_date, status, marked_by)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (student["id"], course_id, class_date,
                         status, session["user_id"])
                    )

            conn.commit()
            flash("Attendance saved successfully!", "success")
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

        # Return to the same course/date so the saved roster remains visible.
        return redirect(url_for(
            "attendance", course_id=course_id, class_date=class_date
        ))

    # GET: show the selected course's enrolled students and any saved status.
    selected_course = request.args.get("course_id", type=int)
    selected_date = request.args.get(
        "class_date", date.today().isoformat()
    )
    roster = []

    if selected_course:
        if faculty_id is not None:
            allowed = query_one(
                "SELECT id FROM courses WHERE id=%s AND faculty_id=%s",
                (selected_course, faculty_id)
            )
            if not allowed:
                abort(403)

        roster = query_all(
            """
            SELECT
                s.id,
                s.roll_no,
                u.name,
                a.status
            FROM enrollments e
            JOIN students s ON s.id=e.student_id
            JOIN users u ON u.id=s.user_id
            LEFT JOIN attendance a
                ON a.student_id=s.id
                AND a.course_id=e.course_id
                AND a.class_date=%s
            WHERE e.course_id=%s
            ORDER BY s.roll_no
            """,
            (selected_date, selected_course)
        )

    return render_template(
        "attendance.html",
        courses=courses,
        roster=roster,
        selected_course=selected_course,
        selected_date=selected_date
    )


# --------------------------------------------------
# MY ATTENDANCE
# --------------------------------------------------

@app.route("/my-attendance")
@role_required("student")
def my_attendance():

    student = query_one(
        """
        SELECT id
        FROM students
        WHERE user_id=%s
        """,
        (session["user_id"],)
    )

    if not student:
        abort(404)

    rows = query_all(
        """
        SELECT
            c.course_code,
            c.course_name,
            COUNT(a.id) AS total_classes,
            COALESCE(
                SUM(a.status='present'), 0
            ) AS present_count,

            COALESCE(
                SUM(a.status='absent'), 0
            ) AS absent_count,

            ROUND(
                100 * COALESCE(
                    SUM(a.status='present'), 0
                ) / NULLIF(COUNT(a.id), 0),
                2
            ) AS percentage

        FROM enrollments e

        JOIN courses c
            ON c.id=e.course_id

        LEFT JOIN attendance a
            ON a.course_id=e.course_id
            AND a.student_id=e.student_id

        WHERE e.student_id=%s

        GROUP BY
            c.id,
            c.course_code,
            c.course_name

        ORDER BY c.course_code
        """,
        (student["id"],)
    )

    return render_template(
        "my_attendance.html",
        attendance=rows
    )


# --------------------------------------------------
# TIMETABLE
# --------------------------------------------------

@app.route("/timetable")
@login_required
def timetable():

    rows = query_all(
        """
        SELECT
            t.id,
            c.course_code,
            c.course_name,
            t.day_of_week,
            t.start_time,
            t.end_time,
            t.room
        FROM timetable t
        JOIN courses c ON c.id=t.course_id

        ORDER BY
            FIELD(
                t.day_of_week,
                'Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday',
                'Sunday'
            ),
            t.start_time
        """
    )

    return render_template(
        "timetable.html",
        timetable=rows
    )


# --------------------------------------------------
# ANNOUNCEMENTS
# --------------------------------------------------

@app.route("/announcements", methods=["GET", "POST"])
@login_required
def announcements():

    if request.method == "POST":

        if session["role"] not in ("admin", "faculty"):
            abort(403)

        title = request.form.get(
            "title", ""
        ).strip()

        message = request.form.get(
            "message", ""
        ).strip()

        if not title or not message:

            flash(
                "Please enter both title and message.",
                "error"
            )

        else:

            execute_query(
                """
                INSERT INTO announcements
                (title, message, created_by)
                VALUES (%s, %s, %s)
                """,
                (
                    title,
                    message,
                    session["user_id"]
                )
            )

            flash(
                "Announcement published successfully.",
                "success"
            )

        return redirect(url_for("announcements"))

    rows = query_all(
        """
        SELECT
            a.id,
            a.title,
            a.message,
            a.created_at,
            u.name AS author
        FROM announcements a
        JOIN users u ON u.id=a.created_by
        ORDER BY a.created_at DESC
        """
    )

    return render_template(
        "announcements.html",
        announcements=rows
    )


# --------------------------------------------------
# LEAVE REQUESTS
# --------------------------------------------------

@app.route("/leave-requests", methods=["GET", "POST"])
@login_required
def leave_requests():

    role = session["role"]

    if request.method == "POST":

        if role != "student":
            abort(403)

        student = query_one(
            """
            SELECT id
            FROM students
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        if not student:
            abort(404)

        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        reason = request.form.get("reason", "").strip()

        if not start_date or not end_date or not reason:

            flash(
                "Please complete all leave request fields.",
                "error"
            )

        elif end_date < start_date:

            flash(
                "End date cannot be before start date.",
                "error"
            )

        else:

            execute_query(
                """
                INSERT INTO leave_requests
                (
                    student_id,
                    start_date,
                    end_date,
                    reason,
                    status
                )
                VALUES (%s, %s, %s, %s, 'pending')
                """,
                (
                    student["id"],
                    start_date,
                    end_date,
                    reason
                )
            )

            flash(
                "Leave request submitted.",
                "success"
            )

        return redirect(url_for("leave_requests"))

    if role == "student":

        student = query_one(
            """
            SELECT id FROM students
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        if not student:
            abort(404)

        rows = query_all(
            """
            SELECT *
            FROM leave_requests
            WHERE student_id=%s
            ORDER BY created_at DESC
            """,
            (student["id"],)
        )

    elif role == "faculty":

        rows = query_all(
            """
            SELECT
                lr.*,
                u.name AS student_name,
                s.roll_no
            FROM leave_requests lr
            JOIN students s ON s.id=lr.student_id
            JOIN users u ON u.id=s.user_id
            ORDER BY lr.created_at DESC
            """
        )

    else:

        rows = query_all(
            """
            SELECT
                lr.*,
                u.name AS student_name,
                s.roll_no
            FROM leave_requests lr
            JOIN students s ON s.id=lr.student_id
            JOIN users u ON u.id=s.user_id
            ORDER BY lr.created_at DESC
            """
        )

    return render_template(
        "leave_requests.html",
        leave_requests=rows
    )


# --------------------------------------------------
# LEAVE REQUEST DECISION
# --------------------------------------------------

@app.route(
    "/leave-requests/<int:request_id>/decision",
    methods=["POST"]
)
@role_required("admin", "faculty")
def leave_request_decision(request_id):

    decision = request.form.get("decision")
    admin_comment = request.form.get("admin_comment", "").strip()

    if decision not in ("approved", "rejected"):
        abort(400)

    # Confirm that the request exists before updating it.
    existing_request = query_one(
        "SELECT id FROM leave_requests WHERE id=%s",
        (request_id,)
    )

    if not existing_request:
        abort(404)

    execute_query(
        """
        UPDATE leave_requests
        SET status=%s, admin_comment=%s
        WHERE id=%s
        """,
        (decision, admin_comment or None, request_id)
    )

    flash(
        "Leave request updated.",
        "success"
    )

    return redirect(url_for("leave_requests"))


# --------------------------------------------------
# COURSE MATERIALS
# --------------------------------------------------

@app.route("/course-materials", methods=["GET", "POST"])
@login_required
def course_materials():

    role = session["role"]

    if request.method == "POST":

        if role not in ("admin", "faculty"):
            abort(403)

        course_id = request.form.get("course_id")
        title = request.form.get("title", "").strip()
        description = request.form.get(
            "description", ""
        ).strip()

        uploaded_file = request.files.get("file")

        if not course_id or not title or not uploaded_file:

            flash(
                "Please complete all required fields.",
                "error"
            )

            return redirect(url_for("course_materials"))

        if role == "faculty":

            faculty = query_one(
                """
                SELECT id FROM faculty
                WHERE user_id=%s
                """,
                (session["user_id"],)
            )

            if not faculty:
                abort(403)

            allowed = query_one(
                """
                SELECT id FROM courses
                WHERE id=%s AND faculty_id=%s
                """,
                (course_id, faculty["id"])
            )

            if not allowed:
                abort(403)

        original_name = secure_filename(
            uploaded_file.filename
        )

        if (
            not original_name
            or "." not in original_name
        ):

            flash("Invalid filename.", "error")

            return redirect(url_for("course_materials"))

        extension = original_name.rsplit(".", 1)[1].lower()

        if extension not in ALLOWED_MATERIAL_EXTENSIONS:

            flash(
                "This file type is not allowed.",
                "error"
            )

            return redirect(url_for("course_materials"))

        stored_name = secure_filename(
            f"{session['user_id']}_{original_name}"
        )

        uploaded_file.save(
            UPLOAD_DIR / stored_name
        )

        execute_query(
            """
            INSERT INTO course_materials
            (
                course_id,
                title,
                description,
                filename,
                uploaded_by
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                course_id,
                title,
                description,
                stored_name,
                session["user_id"]
            )
        )

        flash(
            "Course material uploaded successfully.",
            "success"
        )

        return redirect(url_for("course_materials"))

    if role == "student":

        student = query_one(
            """
            SELECT id FROM students
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        if not student:
            abort(404)

        rows = query_all(
            """
            SELECT
                cm.*,
                c.course_code,
                c.course_name,
                u.name AS uploader
            FROM course_materials cm
            JOIN courses c ON c.id=cm.course_id
            JOIN users u ON u.id=cm.uploaded_by
            JOIN enrollments e ON e.course_id=c.id
            WHERE e.student_id=%s
            ORDER BY cm.created_at DESC
            """,
            (student["id"],)
        )

    else:

        rows = query_all(
            """
            SELECT
                cm.*,
                c.course_code,
                c.course_name,
                u.name AS uploader
            FROM course_materials cm
            JOIN courses c ON c.id=cm.course_id
            JOIN users u ON u.id=cm.uploaded_by
            ORDER BY cm.created_at DESC
            """
        )

    courses = query_all(
        """
        SELECT id, course_code, course_name
        FROM courses
        ORDER BY course_code
        """
    )

    return render_template(
        "course_materials.html",
        materials=rows,
        courses=courses
    )


# --------------------------------------------------
# DOWNLOAD COURSE MATERIAL
# --------------------------------------------------

@app.route(
    "/course-materials/<int:material_id>/download"
)
@login_required
def download_course_material(material_id):

    material = query_one(
        """
        SELECT *
        FROM course_materials
        WHERE id=%s
        """,
        (material_id,)
    )

    if not material:
        abort(404)

    if session["role"] == "student":

        student = query_one(
            """
            SELECT id FROM students
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        if not student:
            abort(403)

        enrolled = query_one(
            """
            SELECT student_id
            FROM enrollments
            WHERE student_id=%s AND course_id=%s
            """,
            (
                student["id"],
                material["course_id"]
            )
        )

        if not enrolled:
            abort(403)

    elif session["role"] == "faculty":

        faculty = query_one(
            """
            SELECT id FROM faculty
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        if not faculty:
            abort(403)

        allowed = query_one(
            """
            SELECT id FROM courses
            WHERE id=%s AND faculty_id=%s
            """,
            (
                material["course_id"],
                faculty["id"]
            )
        )

        if not allowed:
            abort(403)

    return send_from_directory(
        UPLOAD_DIR,
        material["filename"],
        as_attachment=True
    )


# --------------------------------------------------
# ATTENDANCE ALERTS
# --------------------------------------------------

@app.route("/attendance-alerts")
@role_required("student")
def attendance_alerts():

    student = query_one(
        """
        SELECT id
        FROM students
        WHERE user_id=%s
        """,
        (session["user_id"],)
    )

    if not student:
        abort(404)

    rows = query_all(
        """
        SELECT
            c.course_code,
            c.course_name,
            COUNT(a.id) AS total_count,
            SUM(a.status='present') AS present_count,

            ROUND(
                100 * SUM(a.status='present')
                / NULLIF(COUNT(a.id), 0),
                2
            ) AS percentage

        FROM enrollments e

        JOIN courses c
            ON c.id=e.course_id

        LEFT JOIN attendance a
            ON a.course_id=c.id
            AND a.student_id=e.student_id

        WHERE e.student_id=%s

        GROUP BY
            c.id,
            c.course_code,
            c.course_name

        HAVING
            COUNT(a.id)>0
            AND percentage < 75

        ORDER BY percentage
        """,
        (student["id"],)
    )

    return render_template(
        "attendance_alerts.html",
        alerts=rows,
        threshold=75
    )


# --------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------

@app.errorhandler(413)
def upload_too_large(_error):

    flash(
        "The uploaded file is too large. Maximum size is 20 MB.",
        "error"
    )

    return redirect(url_for("course_materials"))


@app.errorhandler(403)
def forbidden(_error):

    return (
        render_template(
            "base.html",
            content_error="You do not have permission to access this page."
        ),
        403
    )


@app.errorhandler(404)
def not_found(_error):

    return (
        render_template(
            "base.html",
            content_error="The requested page was not found."
        ),
        404
    )

# --------------------------------------------------
# ADMIN ENROLLMENT MANAGEMENT
# --------------------------------------------------

@app.route("/enrollment-management", methods=["GET", "POST"])
@role_required("admin")
def enrollment_management():

    if request.method == "POST":

        action = request.form.get("action")

        # ENROLL A STUDENT IN A COURSE
        if action == "enroll":

            student_id = request.form.get("student_id", type=int)
            course_id = request.form.get("course_id", type=int)

            if not student_id or not course_id:
                flash("Please select a student and course.", "error")
                return redirect(url_for("enrollment_management"))

            student = query_one(
                "SELECT id FROM students WHERE id=%s",
                (student_id,)
            )

            course = query_one(
                "SELECT id FROM courses WHERE id=%s",
                (course_id,)
            )

            if not student or not course:
                flash("Invalid student or course.", "error")
            else:
                conn = get_db()
                cur = conn.cursor()

                try:
                    cur.execute(
                        """
                        INSERT IGNORE INTO enrollments
                            (student_id, course_id)
                        VALUES (%s, %s)
                        """,
                        (student_id, course_id)
                    )

                    conn.commit()

                    if cur.rowcount > 0:
                        flash("Student enrolled successfully!", "success")
                    else:
                        flash("Student is already enrolled in this course.", "error")

                except Exception:
                    conn.rollback()
                    raise

                finally:
                    cur.close()
                    conn.close()

        # ASSIGN FACULTY TO A COURSE
        elif action == "assign_faculty":

            course_id = request.form.get("course_id", type=int)
            faculty_id = request.form.get("faculty_id", type=int)

            course = query_one(
                "SELECT id FROM courses WHERE id=%s",
                (course_id,)
            ) if course_id else None

            faculty = query_one(
                "SELECT id FROM faculty WHERE id=%s",
                (faculty_id,)
            ) if faculty_id else None

            if not course or not faculty:
                flash("Please select a valid course and faculty member.", "error")
            else:
                execute_query(
                    """
                    UPDATE courses
                    SET faculty_id=%s
                    WHERE id=%s
                    """,
                    (faculty_id, course_id)
                )

                flash("Faculty assigned successfully!", "success")

        else:
            flash("Invalid action.", "error")

        return redirect(url_for("enrollment_management"))

    # LOAD STUDENTS
    students_list = query_all(
        """
        SELECT
            s.id,
            s.roll_no,
            u.name
        FROM students s
        JOIN users u ON u.id=s.user_id
        ORDER BY u.name
        """
    )

    # LOAD FACULTY
    faculty_list = query_all(
        """
        SELECT
            f.id,
            u.name,
            f.department
        FROM faculty f
        JOIN users u ON u.id=f.user_id
        ORDER BY u.name
        """
    )

    # LOAD COURSES AND ASSIGNED FACULTY
    courses_list = query_all(
        """
        SELECT
            c.id,
            c.course_code,
            c.course_name,
            c.faculty_id,
            u.name AS faculty_name
        FROM courses c
        LEFT JOIN faculty f ON f.id=c.faculty_id
        LEFT JOIN users u ON u.id=f.user_id
        ORDER BY c.course_code
        """
    )

    # LOAD ALL EXISTING ENROLLMENTS
    enrollment_list = query_all(
        """
        SELECT
            e.student_id,
            e.course_id,
            s.roll_no,
            su.name AS student_name,
            c.course_code,
            c.course_name,
            fu.name AS faculty_name
        FROM enrollments e
        JOIN students s ON s.id=e.student_id
        JOIN users su ON su.id=s.user_id
        JOIN courses c ON c.id=e.course_id
        LEFT JOIN faculty f ON f.id=c.faculty_id
        LEFT JOIN users fu ON fu.id=f.user_id
        ORDER BY su.name, c.course_code
        """
    )

    return render_template(
        "enrollment_management.html",
        students=students_list,
        faculty=faculty_list,
        courses=courses_list,
        enrollments=enrollment_list
    )


# --------------------------------------------------
# START APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    app.run(debug=True)
