
from db import get_connection
import sys

conn = get_connection()
try:
    cur = conn.cursor()
    print("Running query...")
    cur.execute("""
        SELECT 
            co.id as outreach_id,
            co.candidate_name,
            co.candidate_email,
            co.resume_id,
            m.id as jd_id,
            m.short_id,
            m.title as role,
            m.metadata->>'created_by' as uploaded_by,
            i.id as interview_id,
            i.interview_date,
            i.confirmed_slot_time,
            i.status as interview_status,
            i.event_link,
            i.meet_link,
            i.selected_slot,
            co.acknowledgement,
            i.feedback_form_link,
            i.feedback_sent_at,
            f.final_recommendation,
            i.interview_round,
            i.hr_round_scheduled,
            i_hr.id as hr_interview_id,
            f_hr.final_recommendation as hr_decision
        FROM candidate_outreach co
        JOIN memories m ON m.id = co.jd_id
        LEFT JOIN interview_schedules i ON i.outreach_id = co.id AND (i.interview_round = 1 OR i.interview_round IS NULL)
        LEFT JOIN feedback f ON f.interview_id = i.id
        LEFT JOIN interview_schedules i_hr ON i_hr.outreach_id = co.id AND i_hr.interview_round = 2
        LEFT JOIN feedback f_hr ON f_hr.interview_id = i_hr.id
    """)
    rows = cur.fetchall()
    print(f"Query successful. Returned {len(rows)} rows.")
except Exception as e:
    print(f"Query FAILED: {e}")
finally:
    conn.close()
