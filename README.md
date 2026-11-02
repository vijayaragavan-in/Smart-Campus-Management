# Smart Campus Management System

## About the Project
Smart Campus Management System is a web-based application developed to simplify and manage academic and administrative activities in educational institutions.

## Technologies Used
- Python
- Flask
- MySQL
- HTML
- CSS
- JavaScript

## Features

### Admin
- Manage student and faculty records.
- Manage courses and enrollments.
- Assign faculty to courses.
- Publish announcements.
- Manage leave requests.

### Faculty
- Manage student attendance.
- View assigned courses.
- Upload course materials.
- Review leave requests.

### Student
- View attendance records.
- Check class timetables.
- Access course materials.
- Submit leave requests.
- Receive low-attendance alerts.
- View announcements.

## Installation and Setup

1. Clone or download the project.
2. Open the project folder in VS Code.
3. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

4. Activate the virtual environment:

   **Windows:**
   ```powershell
   .\.venv\Scripts\activate
   ```

5. Install dependencies:

   ```bash
   pip install Flask mysql-connector-python python-dotenv
   ```

6. Create a MySQL database named `smart_campus`.
7. Configure your database credentials in the `.env` file.
8. Ensure the required database tables are created.
9. Run the application:

   ```bash
   python app.py
   ```

10. Open your browser and visit:

   `http://127.0.0.1:5000`

## Project Structure

```text
Smart Campus Management System/
│
├── app.py
├── .env
├── requirements.txt
├── templates/
├── static/
│   └── uploads/
└── README.md
```

## Database
MySQL is used to store student information, faculty details, courses, enrollments, attendance, timetables, announcements, leave requests, and course materials.

## Author
Smart Campus Management System Project

## License
This project is developed for academic purposes.
