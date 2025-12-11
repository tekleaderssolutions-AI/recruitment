
from db import get_connection

def inspect_constraints():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE conrelid = 'users'::regclass
            AND contype = 'c';
        """)
        constraints = cur.fetchall()
        print("Check constraints on 'users' table:")
        for name, definition in constraints:
            print(f"Constraint: {name}")
            print(f"Definition: {definition}")
            print("-" * 30)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_constraints()
