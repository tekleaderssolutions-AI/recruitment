
from db import get_connection

def debug_data():
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        print("--- Latest 5 Memories (JDs) ---")
        cur.execute("SELECT id, title, user_id, created_at FROM memories ORDER BY created_at DESC LIMIT 5")
        for row in cur.fetchall():
            print(f"Memory: {row}")

        print("\n--- Users ---")
        cur.execute("SELECT id, username, role FROM users")
        for row in cur.fetchall():
            print(f"User: {row}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_data()
