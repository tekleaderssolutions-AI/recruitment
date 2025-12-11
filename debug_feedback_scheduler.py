"""
Debug script to check feedback scheduler status and test conditions.
Run this to diagnose why feedback emails aren't being sent.
"""

from datetime import datetime, timezone, timedelta
from db import get_connection

def check_feedback_scheduler_status():
    """Check if interviews are eligible for feedback emails."""
    
    print("=" * 80)
    print("FEEDBACK SCHEDULER DIAGNOSTIC")
    print("=" * 80)
    print()
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Get current time
        now = datetime.now(timezone.utc)
        cutoff_time = now - timedelta(hours=1)
        
        print(f"Current Time (UTC):        {now}")
        print(f"Cutoff Time (UTC):         {cutoff_time}")
        print(f"  (Interviews before this time should get feedback emails)")
        print()
        
        # Check all scheduled interviews
        print("-" * 80)
        print("ALL SCHEDULED INTERVIEWS:")
        print("-" * 80)
        cur.execute("""
            SELECT 
                i.id,
                i.confirmed_slot_time,
                r.candidate_name,
                m.title as jd_title,
                i.feedback_sent_at,
                i.status
            FROM interview_schedules i
            LEFT JOIN resumes r ON r.id = i.resume_id
            LEFT JOIN memories m ON m.id = i.jd_id
            WHERE i.status = 'scheduled'
              AND i.confirmed_slot_time IS NOT NULL
            ORDER BY i.confirmed_slot_time DESC
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            print("❌ No scheduled interviews found in database")
        else:
            print(f"✓ Found {len(rows)} scheduled interview(s)")
            print()
            for idx, (interview_id, slot_time, candidate_name, jd_title, feedback_sent_at, status) in enumerate(rows, 1):
                print(f"{idx}. Interview ID: {interview_id}")
                print(f"   Candidate:    {candidate_name}")
                print(f"   Job:          {jd_title}")
                print(f"   Status:       {status}")
                print(f"   Slot Time:    {slot_time}")
                print(f"   Feedback Sent: {feedback_sent_at or 'NOT SENT'}")
                
                # Check if eligible
                if slot_time and slot_time <= cutoff_time and not feedback_sent_at:
                    print(f"   ✓ ELIGIBLE for feedback email")
                else:
                    if slot_time and slot_time > cutoff_time:
                        time_remaining = slot_time + timedelta(hours=1) - now
                        minutes_remaining = int(time_remaining.total_seconds() / 60)
                        print(f"   ⏳ NOT YET (wait {minutes_remaining} minutes)")
                    elif feedback_sent_at:
                        print(f"   ✓ Already sent at {feedback_sent_at}")
                print()
        
        print("-" * 80)
        print("INTERVIEWS ELIGIBLE FOR FEEDBACK:")
        print("-" * 80)
        
        # Find interviews needing feedback
        cur.execute("""
            SELECT 
                i.id,
                i.confirmed_slot_time,
                r.candidate_name,
                m.title as jd_title,
                i.feedback_form_link
            FROM interview_schedules i
            JOIN resumes r ON r.id = i.resume_id
            JOIN memories m ON m.id = i.jd_id
            WHERE i.status = 'scheduled'
              AND i.confirmed_slot_time IS NOT NULL
              AND i.confirmed_slot_time <= %s
              AND i.feedback_sent_at IS NULL
            ORDER BY i.confirmed_slot_time ASC
        """, [cutoff_time])
        
        eligible_rows = cur.fetchall()
        
        if not eligible_rows:
            print("❌ No interviews eligible for feedback emails at this time")
        else:
            print(f"✓ {len(eligible_rows)} interview(s) eligible for feedback emails")
            print()
            for idx, (interview_id, slot_time, candidate_name, jd_title, form_link) in enumerate(eligible_rows, 1):
                print(f"{idx}. {candidate_name} - {jd_title}")
                print(f"   Interview was at: {slot_time}")
                print(f"   Form Link: {form_link or 'DEFAULT'}")
                print()
        
        cur.close()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
    
    print("=" * 80)

if __name__ == "__main__":
    check_feedback_scheduler_status()
