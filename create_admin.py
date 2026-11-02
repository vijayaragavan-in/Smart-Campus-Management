import os
import getpass
import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

def main():
    name = input("Admin full name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass.getpass("Admin password (minimum 12 characters): ")
    if not name or not email or len(password) < 12:
        raise SystemExit("Name/email are required and password must be at least 12 characters.")
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "smart_campus"),
    )
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,'admin')",
            (name, email, generate_password_hash(password))
        )
        conn.commit()
        print("Admin account created. Keep the credentials private.")
    except mysql.connector.IntegrityError:
        conn.rollback()
        print("That email already exists.")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
