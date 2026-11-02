-- Run this AFTER the existing schema.sql against the smart_campus database.
USE smart_campus;

CREATE TABLE IF NOT EXISTS leave_requests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  reason TEXT NOT NULL,
  status ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  admin_comment TEXT NULL,
  reviewed_by INT NULL,
  reviewed_at DATETIME NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_leave_student FOREIGN KEY (student_id)
    REFERENCES students(id) ON DELETE CASCADE,
  CONSTRAINT fk_leave_reviewer FOREIGN KEY (reviewed_by)
    REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_leave_status_created (status, created_at)
);

CREATE TABLE IF NOT EXISTS course_materials (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_id INT NOT NULL,
  title VARCHAR(180) NOT NULL,
  description TEXT NULL,
  stored_filename VARCHAR(255) NOT NULL,
  original_filename VARCHAR(255) NOT NULL,
  uploaded_by INT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_material_course FOREIGN KEY (course_id)
    REFERENCES courses(id) ON DELETE CASCADE,
  CONSTRAINT fk_material_uploader FOREIGN KEY (uploaded_by)
    REFERENCES users(id),
  INDEX idx_material_course_created (course_id, created_at)
);
