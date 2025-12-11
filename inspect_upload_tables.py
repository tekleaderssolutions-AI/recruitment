
from db import get_connection

def inspect_tables():
    conn = get_connection()
    try:
        cur = conn.cursor()
        for table in ['memories', 'resumes']:
            cur.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table}';
            """)
            print(f"\nColumns in '{table}' table:")
            for col in cur.fetchall():
                print(col)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_tables()
