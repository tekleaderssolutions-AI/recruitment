import sqlite3
from db import get_connection

try:
    conn = get_connection()
    cur = conn.cursor()
    
    print("--- Candidate Outreach Count ---")
    cur.execute("SELECT count(*) FROM candidate_outreach")
    print(cur.fetchone()[0])
    
    print("\n--- Memories Count ---")
    cur.execute("SELECT count(*) FROM memories")
    print(cur.fetchone()[0])
    
    print("\n--- Join Check (First 5 rows) ---")
    cur.execute("""
        SELECT co.id, co.jd_id, m.id 
        FROM candidate_outreach co 
        LEFT JOIN memories m ON m.id = co.jd_id 
        LIMIT 5
    """)
    rows = cur.fetchall()
    for r in rows:
        print(f"Outreach ID: {r[0]}, Outreach JD_ID: {r[1]}, Memory ID: {r[2]} (Match: {r[1]==r[2]})")

    print("\n--- Raw Outreach Sample ---")
    cur.execute("SELECT id, jd_id FROM candidate_outreach LIMIT 3")
    print(cur.fetchall())

    conn.close()
except Exception as e:
    print(f"Error: {e}")
