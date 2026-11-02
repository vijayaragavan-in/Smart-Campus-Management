
from dotenv import load_dotenv
import os
import mysql.connector
from werkzeug.security import generate_password_hash

load_dotenv(override=True)

db = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME", "smart_campus")
)

cursor = db.cursor()

students = [
    (3, "Niranjan@123"),
    (4, "Niya@123")
]

for user_id, new_password in students:
    password_hash = generate_password_hash(new_password)

    cursor.execute(
        "UPDATE users SET password_hash = %s WHERE id = %s",
        (password_hash, user_id)
    )

    print("Updated user ID:", user_id)
    print("Rows affected:", cursor.rowcount)

db.commit()

cursor.close()
db.close()

print("Both password updates completed!")


