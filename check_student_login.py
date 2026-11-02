
import os
import mysql.connector

from dotenv import load_dotenv
from werkzeug.security import check_password_hash

# Load database settings from .env
load_dotenv(override=True)

try:
    # Connect to MySQL
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "smart_campus")
    )

    print("Database connected successfully!")

    cursor = db.cursor(dictionary=True)

    # Get Niranjan and Niya's accounts
    cursor.execute("""
        SELECT id, name, email, password_hash
        FROM users
        WHERE id IN (3, 4)
        ORDER BY id
    """)

    students = cursor.fetchall()

    test_passwords = {
        3: "Niranjan@123",
        4: "Niya@123"
    }

    if not students:
        print("No student accounts found.")

    for student in students:
        print("\nStudent:", student["name"])
        print("Email:", student["email"])

        password = test_passwords.get(student["id"])

        if password and student["password_hash"]:
            result = check_password_hash(
                student["password_hash"],
                password
            )

            print("Password verification:", result)
        else:
            print("Password hash or test password missing.")

    cursor.close()
    db.close()

except mysql.connector.Error as error:
    print("Database error:", error)

except Exception as error:
    print("Error:", error)
