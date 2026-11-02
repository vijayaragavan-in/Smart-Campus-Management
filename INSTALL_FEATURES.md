# Smart Campus feature upgrade

This patch adds the three requested features to the existing Flask + MySQL project:

1. **Course materials** — faculty/admin upload files; enrolled students can download materials for their courses.
2. **Leave requests** — students submit date-ranged requests; admins approve/reject and can leave a comment.
3. **Attendance alerts** — students can view course-wise alerts when recorded attendance is below 75%.

## Installation

1. Back up your project and database.
2. Replace your existing `app.py` with this upgraded `app.py`.
3. Copy the three HTML files from `templates/` into your project's existing `templates/` directory. Keep your existing templates.
4. Run the SQL migration:
   `mysql -u root -p < feature_migration.sql`
5. Ensure the Flask process can write to `static/uploads/course_materials/`.
6. Run the app as before.

## Add navigation links

Add these links to the authenticated navigation area in your existing `base.html`:

- `url_for('course_materials')` — Course Materials
- `url_for('leave_requests')` — Leave Requests (students and admins)
- `url_for('attendance_alerts')` — Attendance Alerts (students only)

Example:
```html
{% if session.get('user_id') %}
  <a href="{{ url_for('course_materials') }}">Course Materials</a>
  {% if session.get('role') in ('student', 'admin') %}
    <a href="{{ url_for('leave_requests') }}">Leave Requests</a>
  {% endif %}
  {% if session.get('role') == 'student' %}
    <a href="{{ url_for('attendance_alerts') }}">Attendance Alerts</a>
  {% endif %}
{% endif %}
```

## Notes

- Attendance percentage is calculated from attendance records already marked in the database. Courses with no attendance records do not trigger an alert.
- The threshold is currently 75% and is shown in `attendance_alerts.html`.
- Upload limit is 20 MB. Allowed file extensions are PDF, DOC/DOCX, PPT/PPTX, TXT, PNG and JPG/JPEG.
- Uploaded files are stored under `static/uploads/course_materials/`. Back up this directory along with the database.
- This is still an educational starter app. Before public deployment, add CSRF protection, HTTPS, secure session cookie settings, malware scanning for uploaded files, and proper backup/retention policies.
- Your original project did not include its existing HTML templates in the upload, so the three new pages extend your existing `base.html`. You may need to adapt their styling to match your current design.
