import os
import getpass
import mysql.connector
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

def main():
    name = input("Faculty full name: ").strip()
    email = input("Faculty email: ").strip().lower()
    department = input("Department: ").strip()
    password = getpass.getpass("Temporary password (minimum 12 characters): ")
    if not all([name, email, department]) or len(password) < 12:
        raise SystemExit("All fields are required; password must be at least 12 characters.")
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "smart_campus"),
    )
    cur = conn.cursor()
    try:
        conn.start_transaction()
        cur.execute(
            "INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,'faculty')",
            (name, email, generate_password_hash(password))
        )
        user_id = cur.lastrowid
        cur.execute("INSERT INTO faculty (user_id,department) VALUES (%s,%s)", (user_id, department))
        conn.commit()
        print("Faculty account created.")
    except mysql.connector.IntegrityError:
        conn.rollback()
        print("That email already exists.")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
