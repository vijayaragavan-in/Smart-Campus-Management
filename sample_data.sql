USE smart_campus;

-- Optional demo data only. Run after creating a faculty account and student
-- accounts through the app/admin setup. Replace IDs to match your database.
-- Find IDs first:
-- SELECT id,name,email,role FROM users;
-- SELECT id,user_id,department FROM faculty;
-- SELECT id,roll_no FROM students;

-- Example: assign a course to faculty record ID 1.
-- INSERT INTO courses (course_code, course_name, faculty_id)
-- VALUES ('CS101', 'Introduction to Programming', 1);

-- Example: enroll student record ID 1 in course record ID 1.
-- INSERT INTO enrollments (student_id, course_id) VALUES (1, 1);

-- Example: add a timetable entry for course ID 1.
-- INSERT INTO timetable (course_id, day_of_week, start_time, end_time, room)
-- VALUES (1, 'Monday', '09:00:00', '10:00:00', 'Lab 1');

-- To create a faculty user, generate a password hash with Werkzeug in Python,
-- insert the user into users, then insert the resulting users.id into faculty.
