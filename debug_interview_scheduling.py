"""
Debug script to check interview scheduling and email sending.
Run this after a candidate clicks "I'm Interested" to see what happened.
"""
from db import get_connection

def check_interview_schedules():
    """Check recent interview schedules and email status."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        print("=" * 80)
        print("RECENT INTERVIEW SCHEDULES")
        print("=" * 80)
        
        # Get recent interview schedules with outreach info
        cur.execute("""
            SELECT 
                i.id as interview_id,
                i.interview_date,
                i.status,
                i.created_at,
                co.candidate_name,
                co.candidate_email,
                co.acknowledgement,
                co.acknowledged_at,
                m.title as jd_title,
                i.proposed_slots
            FROM interview_schedules i
            LEFT JOIN candidate_outreach co ON co.id = i.outreach_id
            LEFT JOIN memories m ON m.id = i.jd_id
            ORDER BY i.created_at DESC
            LIMIT 10
        """)
        
        schedules = cur.fetchall()
        
        if not schedules:
            print("❌ No interview schedules found")
        else:
            for row in schedules:
                (interview_id, interview_date, status, created_at, 
                 candidate_name, candidate_email, acknowledgement, acknowledged_at,
                 jd_title, proposed_slots) = row
                
                print(f"\nInterview ID: {interview_id}")
                print(f"  Candidate: {candidate_name} ({candidate_email})")
                print(f"  JD: {jd_title}")
                print(f"  Date: {interview_date}")
                print(f"  Status: {status}")
                print(f"  Acknowledgement: {acknowledgement} (at {acknowledged_at})")
                print(f"  Created: {created_at}")
                print(f"  Proposed Slots: {proposed_slots}")
                print("-" * 80)
        
        print("\n" + "=" * 80)
        print("RECENT CANDIDATE OUTREACH")
        print("=" * 80)
        
        # Check candidate outreach records
        cur.execute("""
            SELECT 
                id,
                candidate_name,
                candidate_email,
                acknowledgement,
                acknowledged_at,
                created_at
            FROM candidate_outreach
            WHERE acknowledgement = 'interested'
            ORDER BY acknowledged_at DESC
            LIMIT 10
        """)
        
        outreaches = cur.fetchall()
        
        if not outreaches:
            print("❌ No interested candidates found")
        else:
            print(f"\nFound {len(outreaches)} interested candidates:\n")
            for row in outreaches:
                outreach_id, name, email, ack, ack_at, created_at = row
                print(f"Outreach ID: {outreach_id}")
                print(f"  Candidate: {name} ({email})")
                print(f"  Acknowledged: {ack_at}")
                print(f"  Created: {created_at}")
                
                # Check if interview was scheduled
                cur.execute("""
                    SELECT id, status FROM interview_schedules 
                    WHERE outreach_id = %s
                """, [outreach_id])
                interview = cur.fetchone()
                
                if interview:
                    print(f"  ✅ Interview Scheduled: {interview[0]} (Status: {interview[1]})")
                else:
                    print(f"  ❌ NO INTERVIEW SCHEDULED!")
                print("-" * 80)
                
        cur.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    check_interview_schedules()
