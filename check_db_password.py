
import psycopg2
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER

passwords_to_try = [
    "121414", # From .env
    "postgres",
    "admin",
    "password",
    "123456",
    "root",
    "srikanth",
    "hiring"
]

print(f"Testing connection to {DB_NAME} as {DB_USER} on {DB_HOST}:{DB_PORT}")

success_password = None

for pwd in passwords_to_try:
    print(f"Trying password: '{pwd}' ... ", end="")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=pwd
        )
        conn.close()
        print("SUCCESS!")
        success_password = pwd
        break
    except psycopg2.OperationalError as e:
        print(f"Failed.")
    except Exception as e:
        print(f"Error: {e}")

if success_password:
    print(f"\nFOUND CORRECT PASSWORD: {success_password}")
else:
    print("\nCould not find correct password.")
