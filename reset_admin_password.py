import os
import getpass
import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

email = input("Enter your admin email: ").strip().lower()
new_password = getpass.getpass(
    "Enter new password (minimum 12 characters): "
)

if len(new_password) < 12:
    print("Password must be at least 12 characters.")
    raise SystemExit

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    database=os.getenv("DB_NAME", "smart_campus")
)

try:
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET password_hash=%s WHERE email=%s AND role='admin'",
        (generate_password_hash(new_password), email)
    )
    conn.commit()

    if cur.rowcount:
        print("Admin password reset successfully.")
    else:
        print("No admin account found with that email.")
finally:
    cur.close()
    conn.close()