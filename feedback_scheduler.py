# feedback_scheduler.py
"""
Background scheduler that automatically sends feedback emails to interviewers
1 hour after interview start time.
"""
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional

from db import get_connection
from feedback_email_template import generate_feedback_request_email
from email_sender import send_email
from config import INTERVIEWER_EMAIL, HR_INTERVIEWER_EMAIL, COMPANY_NAME, FEEDBACK_FORM_LINK, INTERVIEW_DURATION_MINUTES


class FeedbackScheduler:
    """Background scheduler for sending interview feedback emails."""
    
    def __init__(self, check_interval_seconds: int = 600):
        """
        Initialize the feedback scheduler.
        
        Args:
            check_interval_seconds: How often to check for pending feedback emails (default: 10 minutes)
        """
        self.check_interval = check_interval_seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the background scheduler thread."""
        if self.running:
            print("[FEEDBACK SCHEDULER] Already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"[FEEDBACK SCHEDULER] Started (checking every {self.check_interval} seconds)")
    
    def stop(self):
        """Stop the background scheduler thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[FEEDBACK SCHEDULER] Stopped")
    
    def _run_loop(self):
        """Main loop that runs in the background thread."""
        while self.running:
            try:
                self._check_and_send_feedback()
            except Exception as e:
                print(f"[FEEDBACK SCHEDULER] Error in loop: {e}")
            
            # Sleep in small increments to allow for clean shutdown
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def _check_and_send_feedback(self):
        """
        Check for interviews that need feedback emails and send them.
        
        Criteria:
        - Status = 'scheduled'
        - Interview start time + 15 minutes <= current time
        - feedback_sent_at IS NULL
        """
        conn = get_connection()
        try:
            cur = conn.cursor()
            
            # Calculate the cutoff time (current time - 15 minutes)
            # Interviews that started more than 15 minutes ago need feedback
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=15)
            
            # Find interviews needing feedback (started more than 15 minutes ago)
            cur.execute(
                """
                SELECT 
                    i.id,
                    i.confirmed_slot_time,
                    r.candidate_name,
                    m.title as jd_title,
                    i.feedback_form_link,
                    i.interview_round
                FROM interview_schedules i
                JOIN resumes r ON r.id = i.resume_id
                JOIN memories m ON m.id = i.jd_id
                WHERE i.status = 'scheduled'
                  AND i.confirmed_slot_time IS NOT NULL
                  AND i.confirmed_slot_time <= %s
                  AND i.feedback_sent_at IS NULL
                ORDER BY i.confirmed_slot_time ASC
                """,
                [cutoff_time]
            )
            
            rows = cur.fetchall()
            
            if not rows:
                print(f"[FEEDBACK SCHEDULER] No feedback emails to send at {datetime.now()}")
                cur.close()
                return
            
            print(f"[FEEDBACK SCHEDULER] Found {len(rows)} interviews needing feedback")
            
            for interview_id, slot_time, candidate_name, jd_title, form_link, interview_round in rows:
                try:
                    self._send_feedback_email(
                        interview_id=interview_id,
                        candidate_name=candidate_name,
                        jd_title=jd_title,
                        slot_time=slot_time,
                        form_link=form_link or FEEDBACK_FORM_LINK,
                        interview_round=interview_round,
                        cur=cur
                    )
                    conn.commit()
                except Exception as e:
                    print(f"[FEEDBACK SCHEDULER] Error sending feedback for {interview_id}: {e}")
                    conn.rollback()
            
            cur.close()
            
        except Exception as e:
            print(f"[FEEDBACK SCHEDULER] Database error: {e}")
        finally:
            conn.close()
    
    def _send_feedback_email(self, interview_id: str, candidate_name: str, jd_title: str, 
                            slot_time: datetime, form_link: str, interview_round: int, cur):
        """
        Send feedback email to interviewer.
        
        Args:
            interview_id: UUID of the interview
            candidate_name: Name of the candidate
            jd_title: Job title
            slot_time: Interview start time
            form_link: Google Form feedback link
            cur: Database cursor
        """
        # Format date and time for email
        interview_date = slot_time.strftime('%A, %B %d, %Y')
        interview_time = slot_time.strftime('%I:%M %p')
        
        # Construct confirmation links
        from config import BASE_URL
        yes_link = f"{BASE_URL}/feedback/confirm/{interview_id}?status=yes"
        no_link = f"{BASE_URL}/feedback/confirm/{interview_id}?status=no"
        
        # Generate email content
        email_content = generate_feedback_request_email(
            candidate_name=candidate_name,
            jd_title=jd_title,
            interview_date=interview_date,
            interview_time=interview_time,
            yes_link=yes_link,
            no_link=no_link,
            company_name=COMPANY_NAME
        )
        
        # Send email to appropriate interviewer based on round
        interviewer_email = HR_INTERVIEWER_EMAIL if (interview_round and interview_round == 2) else INTERVIEWER_EMAIL
        result = send_email(
            to_email=interviewer_email,
            subject=email_content["subject"],
            html_body=email_content["body"]
        )
        
        if result["success"]:
            # Mark feedback as sent
            cur.execute(
                """
                UPDATE interview_schedules
                SET feedback_sent_at = NOW()
                WHERE id = %s
                """,
                [interview_id]
            )
            print(f"[FEEDBACK SCHEDULER] Sent feedback email for interview {interview_id[:8]}... (candidate: {candidate_name})")
        else:
            print(f"[FEEDBACK SCHEDULER] Failed to send feedback for {interview_id}: {result.get('message')}")


# Global scheduler instance
_scheduler_instance: Optional[FeedbackScheduler] = None


def get_scheduler() -> FeedbackScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = FeedbackScheduler(check_interval_seconds=600)  # Check every 10 minutes
    return _scheduler_instance


def start_feedback_scheduler():
    """Start the global feedback scheduler."""
    scheduler = get_scheduler()
    scheduler.start()


def stop_feedback_scheduler():
    """Stop the global feedback scheduler."""
    scheduler = get_scheduler()
    scheduler.stop()
