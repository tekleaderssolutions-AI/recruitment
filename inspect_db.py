
from db import get_connection

def inspect_users_table():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users';
        """)
        columns = cur.fetchall()
        print("Columns in 'users' table:")
        for col in columns:
            print(col)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_users_table()
