# interview_scheduler.py
"""
Interview scheduling agent that coordinates calendar availability and candidate outreach.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
import json

from db import get_connection
from google_calendar import get_available_slots
from interview_email_template import generate_interview_slots_email
from email_sender import send_email
from config import BASE_URL, COMPANY_NAME, INTERVIEWER_EMAIL


def find_first_available_date(num_slots=3, max_days_ahead=30, excluded_dates=None):
    """
    Find the first date with available interview slots, skipping excluded dates.
    
    Args:
        num_slots: Number of slots needed (default: 3)
        max_days_ahead: Maximum days to search ahead (default: 30)
        excluded_dates: List of dates to skip (optional)
    
    Returns:
        datetime object of first available date, or None if no date found
    """
    if excluded_dates is None:
        excluded_dates = []
        
    current_date = datetime.now() + timedelta(days=1)  # Start from tomorrow
    end_date = datetime.now() + timedelta(days=max_days_ahead)
    
    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            current_date += timedelta(days=1)
            continue
            
        # Skip excluded dates
        if current_date.date() in excluded_dates:
            print(f"Skipping {current_date.date()} (already scheduled)")
            current_date += timedelta(days=1)
            continue
        
        try:
            slots = get_available_slots(current_date, num_slots)
            if len(slots) >= num_slots:
                return current_date
        except Exception as e:
            print(f"Error checking {current_date.date()}: {e}")
        
        current_date += timedelta(days=1)
    
    return None


def schedule_interview_for_single_candidate(
    outreach_id: str,
    num_slots: int = 3
) -> Dict[str, Any]:
    """
    Schedule interview for a single candidate (used for automatic scheduling).
    Finds the first available date automatically.
    
    Args:
        outreach_id: Outreach ID of the candidate
        num_slots: Number of time slots to offer (default: 3)
    
    Returns:
        Dictionary with scheduling result
    """
    conn = get_connection()
    
    try:
        cur = conn.cursor()
        
        # Fetch candidate and JD details
        cur.execute(
            """
            SELECT 
                co.id as outreach_id,
                co.resume_id,
                co.candidate_email,
                co.candidate_name,
                co.jd_id,
                r.canonical_json,
                m.title,
                m.canonical_json as jd_json
            FROM candidate_outreach co
            JOIN resumes r ON r.id = co.resume_id
            JOIN memories m ON m.id = co.jd_id
            WHERE co.id = %s
            """,
            [outreach_id]
        )
        
        row = cur.fetchone()
        
        if not row:
            return {"error": "Outreach record not found"}
        
        outreach_id, resume_id, email, name, jd_id, resume_json, jd_title, jd_json = row
        
        # Check if already scheduled
        cur.execute(
            """
            SELECT id FROM interview_schedules
            WHERE outreach_id = %s AND status NOT IN ('cancelled', 'declined')
            """,
            [outreach_id]
        )
        
        if cur.fetchone():
            return {"message": "Interview already scheduled for this candidate"}
            
        # Fetch dates that are already taken by other candidates
        cur.execute(
            """
            SELECT DISTINCT interview_date 
            FROM interview_schedules 
            WHERE status NOT IN ('cancelled', 'declined')
            """
        )
        busy_dates = [row[0] for row in cur.fetchall()]
        
        # Find first available date (excluding busy dates)
        interview_date = find_first_available_date(num_slots, excluded_dates=busy_dates)
        
        if not interview_date:
            return {"error": "No available dates found in the next 30 days"}
        
        # Fetch available time slots
        try:
            time_slots = get_available_slots(interview_date, num_slots)
            
            if not time_slots:
                return {"error": "No available time slots found"}
        except Exception as e:
            return {"error": f"Failed to fetch calendar availability: {str(e)}"}
        
        # Prepare data
        interview_id = str(uuid.uuid4())
        
        candidate_data = {
            "candidate_name": name,
            "email": email,
            "canonical_json": resume_json
        }
        
        jd_data = {
            "id": jd_id,
            "title": jd_title,
            "canonical_json": jd_json,
            "role": jd_json.get("role") if jd_json else "Position"
        }
        
        # Generate email with time slots
        email_content = generate_interview_slots_email(
            candidate_data=candidate_data,
            jd_data=jd_data,
            interview_id=interview_id,
            outreach_id=outreach_id,
            date=interview_date,
            time_slots=time_slots,
            base_url=BASE_URL,
            company_name=COMPANY_NAME
        )
        
        # Send email with interviewer CC'd
        send_result = send_email(
            to_email=email,
            subject=email_content["subject"],
            html_body=email_content["body"],
            cc_email=INTERVIEWER_EMAIL  # CC the interviewer
        )
        
        if send_result["success"]:
            # Store interview schedule in database
            proposed_slots_data = {
                "slot1": {
                    "start": time_slots[0]['start_time'].isoformat(),
                    "end": time_slots[0]['end_time'].isoformat()
                },
                "slot2": {
                    "start": time_slots[1]['start_time'].isoformat(),
                    "end": time_slots[1]['end_time'].isoformat()
                } if len(time_slots) > 1 else None,
                "slot3": {
                    "start": time_slots[2]['start_time'].isoformat(),
                    "end": time_slots[2]['end_time'].isoformat()
                } if len(time_slots) > 2 else None
            }
            
            cur.execute(
                """
                INSERT INTO interview_schedules 
                (id, resume_id, jd_id, outreach_id, interview_date, 
                 proposed_slots, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, NOW())
                """,
                [
                    interview_id,
                    resume_id,
                    jd_id,
                    outreach_id,
                    interview_date.date(),
                    json.dumps(proposed_slots_data),
                    'pending'
                ]
            )
            conn.commit()
            
            return {
                "success": True,
                "interview_id": interview_id,
                "interview_date": interview_date.strftime('%Y-%m-%d'),
                "candidate_name": name,
                "email": email
            }
        else:
            return {"error": send_result["message"]}
            
    except Exception as e:
        return {"error": f"Error scheduling interview: {str(e)}"}
    finally:
        conn.close()


def schedule_interviews_for_interested_candidates(
    jd_id: str,
    interview_date: datetime,
    num_slots: int = 3
) -> Dict[str, Any]:
    """
    Schedule interviews for all interested candidates for a given JD.
    
    Args:
        jd_id: Job description ID
        interview_date: Date for the interviews
        num_slots: Number of time slots to offer (default: 3)

We have now copied several files into structured folders. I'll continue copying the remaining groups (core, agents, integrations, scripts) and then commit the reorganized copies. Next I'll update the todo list status. After the next 3 file operations I'll provide a short progress update and what's next.  I'll proceed to copy a few more files (db, migrations, config, interview_email_template, trigger_interview_schedule, embeddings, calendar_utils, oauth tool, ranking, ranking helpers).  ` (truncated)`}{