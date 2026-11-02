CREATE DATABASE IF NOT EXISTS smart_campus
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_campus;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin','faculty','student') NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  roll_no VARCHAR(30) NOT NULL UNIQUE,
  department VARCHAR(100) NOT NULL,
  semester TINYINT NOT NULL,
  CONSTRAINT fk_students_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS faculty (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  department VARCHAR(100) NOT NULL,
  CONSTRAINT fk_faculty_user FOREIGN KEY (user_id)
    REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS courses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_code VARCHAR(20) NOT NULL UNIQUE,
  course_name VARCHAR(120) NOT NULL,
  faculty_id INT NULL,
  CONSTRAINT fk_courses_faculty FOREIGN KEY (faculty_id)
    REFERENCES faculty(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS enrollments (
  student_id INT NOT NULL,
  course_id INT NOT NULL,
  PRIMARY KEY (student_id, course_id),
  CONSTRAINT fk_enroll_student FOREIGN KEY (student_id)
    REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_enroll_course FOREIGN KEY (course_id)
    REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS attendance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  course_id INT NOT NULL,
  class_date DATE NOT NULL,
  status ENUM('present','absent') NOT NULL,
  marked_by INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_attendance (student_id, course_id, class_date),
  CONSTRAINT fk_att_student FOREIGN KEY (student_id)
    REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_att_course FOREIGN KEY (course_id)
    REFERENCES courses(id) ON DELETE CASCADE,
  CONSTRAINT fk_att_marker FOREIGN KEY (marked_by)
    REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS timetable (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_id INT NOT NULL,
  day_of_week ENUM('Monday','Tuesday','Wednesday','Thursday',
                   'Friday','Saturday','Sunday') NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  room VARCHAR(40),
  CONSTRAINT fk_timetable_course FOREIGN KEY (course_id)
    REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS announcements (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(180) NOT NULL,
  message TEXT NOT NULL,
  created_by INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_notice_creator FOREIGN KEY (created_by)
    REFERENCES users(id)
);
