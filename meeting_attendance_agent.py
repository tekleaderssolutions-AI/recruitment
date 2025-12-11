from datetime import datetime, timezone
from typing import Dict, Any

from db import get_connection
from google_calendar import get_calendar_service
from config import INTERVIEWER_EMAIL


def check_attendance_for_interview(interview_id: str) -> Dict[str, Any]:
    """
    Check calendar RSVP / attendance-style status for a given interview.
    NOTE: Google Calendar API can tell us who accepted/declined the invite,
    but NOT who is actually live in the Meet at this moment. This function
    therefore reports invitation response status + timing.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT i.event_id,
                   i.interview_date,
                   i.confirmed_slot_time,
                   r.email AS candidate_email,
                   r.candidate_name
            FROM interview_schedules i
            JOIN resumes r ON r.id = i.resume_id
            WHERE i.id = %s
            """,
            [interview_id],
        )
        row = cur.fetchone()
        cur.close()

        if not row:
            return {"error": "Interview not found", "interview_id": interview_id}

        event_id, interview_date, confirmed_slot_time, candidate_email, candidate_name = row
        if not event_id:
            return {"error": "No calendar event stored for this interview", "interview_id": interview_id}

        service = get_calendar_service()
        event = service.events().get(calendarId=INTERVIEWER_EMAIL, eventId=event_id).execute()

        attendees = event.get("attendees", [])
        attendee_status = {}
        for a in attendees:
            email = a.get("email")
            status = a.get("responseStatus")
            if email:
                attendee_status[email] = status

        now_utc = datetime.now(timezone.utc)
        start_str = event.get("start", {}).get("dateTime")
        end_str = event.get("end", {}).get("dateTime")
        window_state = "unknown"
        if start_str and end_str:
            try:
                start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                if now_utc < start_dt:
                    window_state = "before_meeting"
                elif start_dt <= now_utc <= end_dt:
                    window_state = "during_meeting"
                else:
                    window_state = "after_meeting"
            except Exception:
                pass

        return {
            "success": True,
            "interview_id": interview_id,
            "event_id": event_id,
            "window_state": window_state,
            "candidate": {
                "email": candidate_email,
                "name": candidate_name,
                "response_status": attendee_status.get(candidate_email),
            },
            "interviewer": {
                "email": INTERVIEWER_EMAIL,
                "response_status": attendee_status.get(INTERVIEWER_EMAIL),
            },
            "raw_attendees": attendee_status,
        }
    except Exception as e:
        return {"error": f"Failed to check attendance: {e}", "interview_id": interview_id}
    finally:
        conn.close()


