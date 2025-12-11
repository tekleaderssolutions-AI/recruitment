# main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional, List, Dict, Any
import pdfplumber
from io import BytesIO

from jd_agent import analyze_job_description
from ranker_agent import get_top_matches_for_role
from resume_agent import process_resume_text
import html


# --- Authentication Logic ---
import os
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import status



def authenticate_user(username: str, password: str) -> Optional[dict]:
    admin_username = os.getenv("ADMIN_USERNAME", "hiring")
    admin_password = os.getenv("ADMIN_PASSWORD", "Akshitha@73")
    
    print(f"DEBUG: Attempting login with username='{username}'")
    
    if username == admin_username and password == admin_password:
        print("DEBUG: Login successful!")
        return {
            "id": "admin", 
            "username": admin_username, 
            "password_hash": admin_password
        }
    print("DEBUG: Login failed - credentials do not match")
    return None


# ---------------------------


 
app = FastAPI(title="JD Analyzer Agent")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Start the feedback scheduler when the application starts
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on application startup."""
    from feedback_scheduler import start_feedback_scheduler
    start_feedback_scheduler()
    print("[STARTUP] Feedback scheduler started")


# Serve the minimal UI from ./static
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_index():
    return FileResponse("static/index.html")


@app.post("/init-db")
def init_db_endpoint():
    """Run DB migrations (requires DB user to have extension creation rights).

    This endpoint is intentionally unprotected in this minimal example —
    in production protect it with auth.
    """
    try:
        import migrations

        migrations.init_db()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"status": "ok", "message": "migrations run"}
 
@app.get("/debug")
def debug():
    import os
    return {
        "OPENROUTER_API_KEY_present": bool(os.environ.get("OPENROUTER_API_KEY")),
        "CHAT_MODEL": os.environ.get("CHAT_MODEL"),
        "EMBEDDING_MODEL": os.environ.get("EMBEDDING_MODEL"),
    }

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint that returns a simple access token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Return username as token (simple approach without JWT)
    return {"access_token": user["username"], "token_type": "bearer"}


@app.get("/feedback-responses-link")
async def get_feedback_responses_link():
    """Redirect to Google Sheets with feedback responses."""
    from config import FEEDBACK_RESPONSES_SHEET_LINK
    from fastapi.responses import RedirectResponse, HTMLResponse
    
    if FEEDBACK_RESPONSES_SHEET_LINK and FEEDBACK_RESPONSES_SHEET_LINK != "PASTE_YOUR_GOOGLE_SHEETS_RESPONSES_LINK_HERE":
        return RedirectResponse(url=FEEDBACK_RESPONSES_SHEET_LINK)
    else:
        html = """
        <html>
        <head><title>Feedback Responses</title></head>
        <body style="font-family: Arial; padding: 40px; text-align: center;">
            <h2>⚠️ Feedback Responses Sheet Not Configured</h2>
            <p>Please update <code>FEEDBACK_RESPONSES_SHEET_LINK</code> in config.py with your Google Sheets link.</p>
            <p><strong>How to get the link:</strong></p>
            <ol style="text-align: left; max-width: 600px; margin: 20px auto;">
                <li>Open your Google Form</li>
                <li>Click "Responses" tab</li>
                <li>Click the green Sheets icon to create/open the responses spreadsheet</li>
                <li>Copy the URL from your browser</li>
                <li>Paste it in config.py</li>
            </ol>
            <button onclick="history.back()" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">← Go Back</button>
        </body>
        </html>
        """
        return HTMLResponse(content=html)


@app.get("/feedback/confirm/{interview_id}")
async def confirm_feedback_status(interview_id: str, status: str):
    """
    Handle feedback confirmation from email.
    
    Args:
        interview_id: UUID of the interview
        status: 'yes' or 'no'
    """
    from fastapi.responses import RedirectResponse, HTMLResponse
    from db import get_connection
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Update status based on response
        if status.lower() == 'yes':
            # Mark interview as completed
            cur.execute(
                """
                UPDATE interview_schedules
                SET status = 'completed', updated_at = NOW()
                WHERE id = %s
                RETURNING interview_round
                """,
                [interview_id]
            )
            row = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()
            
            interview_round = row[0] if row else 1
            
            # Redirect to appropriate feedback form
            if interview_round == 2:
                return RedirectResponse(url=f"/static/hr-feedback-form.html?id={interview_id}", status_code=303)
            else:
                return RedirectResponse(url=f"/static/feedback-form.html?id={interview_id}", status_code=303)
        else:
            # Interview didn't happen - keep status as scheduled
            cur.close()
            conn.close()
            
            html_response = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Thank You</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    }
                    .container {
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        text-align: center;
                        max-width: 500px;
                    }
                    .icon {
                        font-size: 64px;
                        margin-bottom: 20px;
                    }
                    h1 {
                        color: #1f2937;
                        margin-bottom: 20px;
                    }
                    p {
                        color: #6b7280;
                        line-height: 1.6;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="icon">📋</div>
                    <h1>Thank You</h1>
                    <p>We've recorded that the interview has not happened yet. No further action is needed at this time.</p>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_response)
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/interview/{interview_id}")
async def get_interview_details(interview_id: str):
    """
    Get interview details for pre-filling the feedback form.
    
    Args:
        interview_id: UUID of the interview
        
    Returns:
        JSON with candidate_name, jd_title, interview_date, interview_time
    """
    from db import get_connection
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                r.candidate_name,
                m.title as jd_title,
                i.confirmed_slot_time,
                r.email,
                m.short_id
            FROM interview_schedules i
            JOIN resumes r ON r.id = i.resume_id
            JOIN memories m ON m.id = i.jd_id
            WHERE i.id = %s
        """, [interview_id])
        
        row = cur.fetchone()
        
        if not row:
            return JSONResponse({"error": "Interview not found"}, status_code=404)
        
        candidate_name, jd_title, confirmed_slot_time, candidate_email, jd_short_id = row
        
        # Format date and time
        interview_date = confirmed_slot_time.strftime('%A, %B %d, %Y') if confirmed_slot_time else 'N/A'
        interview_time = confirmed_slot_time.strftime('%I:%M %p') if confirmed_slot_time else 'N/A'
        
        return {
            "candidate_name": candidate_name,
            "jd_title": jd_title,
            "jd_id": jd_short_id or 'N/A',
            "interview_date": interview_date,
            "interview_time": interview_time,
            "candidate_email": candidate_email
        }
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()


@app.post("/api/feedback/submit")
async def submit_feedback(request: Dict[str, Any]):
    """
    Submit interview feedback to database.
    
    Expected JSON body:
    {
        "interview_id": "uuid",
        "technical_skills": 1-10,
        "education_training": 1-10,
        "work_experience": 1-10,
        "organizational_skills": 1-10,
        "communication": 1-10,
        "attitude": 1-10,
        "overall_rating": 1-10,
        "final_recommendation": "string",
        "comments": "string"
    }
    """
    from db import get_connection
    from config import INTERVIEWER_EMAIL
    
    try:
        interview_id = request.get("interview_id")
        
        # Get interview details for applicant_name and interview_date
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                r.candidate_name,
                i.confirmed_slot_time
            FROM interview_schedules i
            JOIN resumes r ON r.id = i.resume_id
            WHERE i.id = %s
        """, [interview_id])
        
        interview_row = cur.fetchone()
        if not interview_row:
            return JSONResponse({"success": False, "error": "Interview not found"}, status_code=404)
        
        candidate_name, confirmed_slot_time = interview_row
        interview_date = confirmed_slot_time.date() if confirmed_slot_time else None
        
        # Insert feedback into database
        cur.execute("""
            INSERT INTO feedback (
                interview_id,
                timestamp,
                applicant_name,
                interview_date,
                interviewer,
                interview_type,
                job_opening_id,
                technical_skills,
                education_training,
                work_experience,
                organizational_skills,
                communication,
                attitude,
                overall_rating,
                final_recommendation,
                comments
            ) VALUES (
                %s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, [
            interview_id,
            candidate_name,
            interview_date,
            INTERVIEWER_EMAIL,
            request.get("interview_type", ""),
            request.get("job_opening_id", ""),
            float(request.get("technical_skills")),
            float(request.get("education_training")),
            float(request.get("work_experience")),
            float(request.get("organizational_skills")),
            float(request.get("communication")),
            float(request.get("attitude")),
            float(request.get("overall_rating")),
            request.get("final_recommendation"),
            request.get("comments", "")
        ])
        
        conn.commit()
        cur.close()
        conn.close()
        
        # If this is HR Round feedback, send decision emails automatically
        interview_type = request.get("interview_type", "")
        final_recommendation = request.get("final_recommendation")
        
        if interview_type == "HR Round" and final_recommendation:
            try:
                # Get candidate email
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT r.email, r.candidate_name, j.title
                    FROM interview_schedules i
                    JOIN resumes r ON r.id = i.resume_id
                    LEFT JOIN memories j ON j.id = i.jd_id
                    WHERE i.id = %s
                """, [interview_id])
                
                candidate_row = cur.fetchone()
                cur.close()
                conn.close()
                
                if candidate_row:
                    candidate_email, candidate_name, position = candidate_row
                    
                    # Parse HR feedback details from comments
                    comments = request.get("comments", "")
                    
                    def parse_field(field_name):
                        import re
                        regex = re.compile(f"{field_name}:\\s*(.+?)(?=\\n|$)", re.IGNORECASE)
                        match = regex.search(comments)
                        return match.group(1).strip() if match else "N/A"
                    
                    offered_package = parse_field("Offered Package")
                    joining_date = parse_field("Date of Joining")
                    
                    if final_recommendation == "Hire":
                        # Send congratulations email with offer letter PDF
                        from hr_decision_emails import generate_congratulations_email
                        from offer_letter_generator import generate_offer_letter_pdf
                        from email_sender import send_email
                        
                        # Generate offer letter PDF
                        pdf_bytes = generate_offer_letter_pdf(
                            candidate_name=candidate_name,
                            position=position or "AI Engineer (Trainee)",
                            ctc=offered_package if offered_package != "N/A" else "As per discussion",
                            joining_date=joining_date if joining_date != "N/A" else "To be confirmed"
                        )
                        
                        # Generate email
                        email_data = generate_congratulations_email(
                            candidate_name=candidate_name,
                            position=position or "AI Engineer (Trainee)",
                            ctc=offered_package if offered_package != "N/A" else "As per discussion",
                            joining_date=joining_date if joining_date != "N/A" else "To be confirmed"
                        )
                        
                        # Send email with PDF attachment
                        send_email(
                            to_email=candidate_email,
                            subject=email_data["subject"],
                            body=email_data["body"],
                            attachment_data=pdf_bytes,
                            attachment_filename=f"Offer_Letter_{candidate_name.replace(' ', '_')}.pdf"
                        )
                        
                        print(f"✅ Sent offer letter to {candidate_email}")
                        
                    elif final_recommendation == "Reject":
                        # Send rejection email
                        from hr_decision_emails import generate_rejection_email
                        from email_sender import send_email
                        
                        email_data = generate_rejection_email(
                            candidate_name=candidate_name,
                            position=position or "the position"
                        )
                        
                        send_email(
                            to_email=candidate_email,
                            subject=email_data["subject"],
                            body=email_data["body"]
                        )
                        
                        print(f"✅ Sent rejection email to {candidate_email}")
                        
            except Exception as email_error:
                print(f"⚠️ Error sending HR decision email: {email_error}")
                # Don't fail the feedback submission if email fails
        
        return {"success": True, "message": "Feedback submitted successfully"}
        
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/api/feedback/view/{interview_id}")
async def view_feedback(interview_id: str):
    """
    Retrieve feedback for a specific interview.
    
    Returns feedback data including all ratings and comments.
    """
    from db import get_connection
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Fetch feedback for the interview
        cur.execute("""
            SELECT 
                technical_skills,
                education_training,
                work_experience,
                organizational_skills,
                communication,
                attitude,
                overall_rating,
                final_recommendation,
                comments,
                interview_type
            FROM feedback
            WHERE interview_id = %s
        """, [interview_id])
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return {"feedback": None}
        
        # Map database columns to response
        feedback = {
            "technical_skills": row[0],
            "education_training": row[1],
            "work_experience": row[2],
            "organizational_skills": row[3],
            "communication": row[4],
            "attitude": row[5],
            "overall_rating": row[6],
            "final_recommendation": row[7],
            "comments": row[8],
            "additional_comments": row[8],  # Alias for compatibility
            "interview_type": row[9]
        }
        
        return {"feedback": feedback}
        
    except Exception as e:
        print(f"Error fetching feedback: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/recruit/send-hr-decision")
async def send_hr_decision_email(request: Dict[str, Any]):
    """
    Manually send offer email with PDF attachment.
    """
    from db import get_connection
    from hr_decision_emails import generate_congratulations_email
    from offer_letter_generator import generate_offer_letter_pdf
    from email_sender import send_email
    
    try:
        # Debug logging
        import logging
        logging.basicConfig(filename='email_debug.log', level=logging.INFO, 
                          format='%(asctime)s - %(levelname)s - %(message)s')
        
        logging.info(f"Received request to send HR decision for interview_id: {request.get('interview_id')}")
        
        interview_id = request.get("interview_id")
        if not interview_id:
            logging.error("Interview ID missing")
            return JSONResponse({"success": False, "error": "Interview ID required"}, status_code=400)
            
        conn = get_connection()
        cur = conn.cursor()
        
        # Get candidate details and feedback
        cur.execute("""
            SELECT r.email, r.email, r.candidate_name, j.title, f.comments, f.final_recommendation
            FROM interview_schedules i
            JOIN resumes r ON r.id = i.resume_id
            LEFT JOIN memories j ON j.id = i.jd_id
            LEFT JOIN feedback f ON f.interview_id = i.id
            WHERE i.id = %s
        """, [interview_id])
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
             logging.error(f"Interview not found or no resume linked for id: {interview_id}")
             return JSONResponse({"success": False, "error": "Interview not found"}, status_code=404)
        
        # Handle cases where candidate_email might be in different columns (r.candidate_email vs r.email)
        candidate_email_1, candidate_email_2, candidate_name, position, comments, recommendation = row
        candidate_email = candidate_email_1 or candidate_email_2
        
        logging.info(f"Found candidate: {candidate_name}, Email: {candidate_email}, Position: {position}")
        
        if not candidate_email:
            logging.error("Candidate email is missing in database")
            return JSONResponse({"success": False, "error": "Candidate email not found"}, status_code=400)
        
        if not comments:
            comments = ""
            
        # Parse package details
        def parse_field(field_name):
            import re
            regex = re.compile(f"{field_name}:\\s*(.+?)(?=\\n|$)", re.IGNORECASE)
            match = regex.search(comments)
            return match.group(1).strip() if match else "N/A"
        
        offered_package = parse_field("Offered Package")
        joining_date = parse_field("Date of Joining")
        
        logging.info(f"Generating PDF for {candidate_name} with Package: {offered_package}")
        
        # Generate offer letter PDF
        pdf_bytes = generate_offer_letter_pdf(
            candidate_name=candidate_name,
            position=position or "AI Engineer (Trainee)",
            ctc=offered_package if offered_package != "N/A" else "As per discussion",
            joining_date=joining_date if joining_date != "N/A" else "To be confirmed"
        )
        
        logging.info("PDF Generated successfully")
        
        # Generate email
        email_data = generate_congratulations_email(
            candidate_name=candidate_name,
            position=position or "AI Engineer (Trainee)",
            ctc=offered_package if offered_package != "N/A" else "As per discussion",
            joining_date=joining_date if joining_date != "N/A" else "To be confirmed"
        )
        
        logging.info("Sending email via SMTP...")
        
        # Send email with PDF attachment
        result = send_email(
            to_email=candidate_email,
            subject=email_data["subject"],
            body=email_data["body"],
            attachment_data=pdf_bytes,
            attachment_filename=f"Offer_Letter_{candidate_name.replace(' ', '_')}.pdf"
        )
        
        logging.info(f"SMTP Result: {result}")
        
        if not result.get("success"):
            return JSONResponse({"success": False, "error": result.get("message")}, status_code=500)
        
        return {"success": True, "message": f"Offer email sent to {candidate_email}"}
        
    except Exception as e:
        import traceback
        logging.error(f"Error sending HR decision email: {e}")
        logging.error(traceback.format_exc())
        print(f"Error sending HR decision email: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/api/send-decision-email")
async def send_decision_email(request: Dict[str, Any]):
    """
    Manually send rejection email to candidate.
    Handles 'Reject' (HR) or 'Not Selected' (Technical) recommendations.
    """
    from db import get_connection
    from hr_decision_emails import generate_rejection_email
    from email_sender import send_email
    
    try:
        interview_id = request.get("interview_id")
        
        if not interview_id:
            return JSONResponse({"success": False, "error": "interview_id is required"}, status_code=400)
        
        conn = get_connection()
        cur = conn.cursor()
        
        # Get feedback and candidate details
        cur.execute("""
            SELECT 
                f.final_recommendation,
                r.candidate_name,
                r.email,
                j.title
            FROM feedback f
            JOIN interview_schedules i ON i.id = f.interview_id
            JOIN resumes r ON r.id = i.resume_id
            LEFT JOIN memories j ON j.id = i.jd_id
            WHERE f.interview_id = %s
            ORDER BY f.timestamp DESC
            LIMIT 1
        """, [interview_id])
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return JSONResponse({"success": False, "error": "Feedback not found for this interview"}, status_code=404)
        
        final_recommendation, candidate_name, candidate_email, jd_title = row
        
        # Determine email type based on recommendation
        if final_recommendation in ["Reject", "Not Selected", "Do Not Hire"]:
             email_data = generate_rejection_email(
                candidate_name=candidate_name,
                position=jd_title or "the position"
            )
             
             send_email(
                to_email=candidate_email,
                subject=email_data["subject"],
                body=email_data["body"]
            )
             
             return {"success": True, "message": f"Rejection email sent to {candidate_email}"}
        else:
             return JSONResponse({
                "success": False, 
                "error": f"This endpoint is only for rejections. Use 'Send Offer Email' for offers. Status: {final_recommendation}"
            }, status_code=400)
            
    except Exception as e:
        print(f"Error sending decision email: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)



@app.post("/sync-feedback-csv")
async def sync_feedback_csv(file: UploadFile = File(...)):
    """
    Upload CSV export from Google Sheets and sync to feedback table.
    Users should:
    1. Open the Google Sheets
    2. File -> Download -> CSV
    3. Upload here
    """
    import csv
    from io import StringIO
    from datetime import datetime
    from db import get_connection
    
    try:
        # Read the uploaded CSV
        contents = await file.read()
        csv_text = contents.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_text))
        
        conn = get_connection()
        cur = conn.cursor()
        
        # Ensure columns are NUMERIC to handle decimals (e.g. 4.5)
        # This is a safe operation to run repeatedly
        numeric_cols = [
            'technical_skills', 'education_training', 'work_experience', 
            'organizational_skills', 'communication', 'attitude', 'overall_rating'
        ]
        for col in numeric_cols:
            cur.execute(f"""
                DO $$ 
                BEGIN 
                    BEGIN
                        ALTER TABLE feedback ALTER COLUMN {col} TYPE NUMERIC(4, 1);
                    EXCEPTION
                        WHEN OTHERS THEN NULL;
                    END;
                END $$;
            """)
        conn.commit()
        
        # Clear existing feedback data (or you can skip this to keep historical data)
        # cur.execute("DELETE FROM feedback")
        
        inserted_count = 0
        skipped_count = 0
        errors = []
        
        for i, row in enumerate(csv_reader):
            try:
                # Parse the row data
                timestamp_str = row.get('Timestamp', '')
                applicant_name = row.get('Applicant Name', '')
                interview_date_str = row.get('Interview Date', '')
                interviewer = row.get('Interviewer', '')
                interview_type = row.get('Interview Type', '')
                job_opening_id = row.get('Job Opening ID', '')
                
                # Parse ratings (handle empty strings and decimals)
                def parse_rating(val):
                    if not val:
                        return 0.0
                    try:
                        return float(val)
                    except ValueError:
                        return 0.0

                technical_skills = parse_rating(row.get('Technical Skills'))
                education_training = parse_rating(row.get('Education/Training'))
                work_experience = parse_rating(row.get('Work Experience'))
                organizational_skills = parse_rating(row.get('Organizational Skills'))
                communication = parse_rating(row.get('Communication'))
                attitude = parse_rating(row.get('Attitude'))
                overall_rating = parse_rating(row.get('Overall Rating'))
                
                final_recommendation = row.get('Final recommendation', '')
                comments = row.get('Comments', '')
                
                # Parse dates
                timestamp = None
                if timestamp_str:
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%m/%d/%Y %H:%M:%S')
                    except:
                        try:
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                
                interview_date = None
                if interview_date_str:
                    try:
                        interview_date = datetime.strptime(interview_date_str, '%m/%d/%Y').date()
                    except:
                        try:
                            interview_date = datetime.strptime(interview_date_str, '%Y-%m-%d').date()
                        except:
                            pass
                
                # Insert into database
                cur.execute("""
                    INSERT INTO feedback (
                        timestamp, applicant_name, interview_date, interviewer, 
                        interview_type, job_opening_id, technical_skills, 
                        education_training, work_experience, organizational_skills,
                        communication, attitude, overall_rating, 
                        final_recommendation, comments
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    timestamp, applicant_name, interview_date, interviewer,
                    interview_type, job_opening_id, technical_skills,
                    education_training, work_experience, organizational_skills,
                    communication, attitude, overall_rating,
                    final_recommendation, comments
                ))
                
                inserted_count += 1
                
            except Exception as e:
                error_msg = f"Row {i+1}: {str(e)}"
                print(f"Error processing row: {e}")
                errors.append(error_msg)
                skipped_count += 1
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"Successfully synced {inserted_count} feedback records",
            "inserted": inserted_count,
            "skipped": skipped_count,
            "errors": errors[:5]  # Return first 5 errors
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


 
def _extract_pdf_text(contents: bytes) -> str:
    with pdfplumber.open(BytesIO(contents)) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])


 
 
@app.post("/jd/analyze/pdf")
async def analyze_jd_pdf(
    job_id: Optional[str] = Form(default=None),
    source_url: Optional[str] = Form(default=None),
    file: UploadFile = File(...),   # required PDF
):
    """
    Analyze JD from uploaded PDF file.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
 
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded PDF is empty")
 
        raw_jd_text = _extract_pdf_text(contents)
 
        if not raw_jd_text.strip():
            raise HTTPException(status_code=400, detail="JD text is empty after PDF extraction")
 
        memory_json = analyze_job_description(
            raw_jd_text=raw_jd_text,
            job_id=job_id,
            source_url=source_url,
            created_by="jd_analyzer_agent_pdf",
        )
        
        # Add the database ID to the response for embedding-based matching
        # The memory_json already contains 'id' from jd_memory.create_memory
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error (pdf): {e}")
 
    return memory_json
 
 
@app.post("/resumes/upload")
async def upload_resumes(
    files: List[UploadFile] = File(...),
    source_url: Optional[str] = Form(default=None),
):
    """
    Upload MULTIPLE resume PDFs.
    For each:
      - Extract text
      - Parse with LLM
      - Store resume + vector
    Returns basic info for UI.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    results: List[Dict[str, Any]] = []

    for file in files:
        filename = file.filename

        if not filename.lower().endswith(".pdf"):
            results.append({
                "file_name": filename,
                "status": "skipped",
                "reason": "not a PDF",
            })
            continue

        try:
            contents = await file.read()
            if not contents:
                results.append({
                    "file_name": filename,
                    "status": "error",
                    "reason": "empty file",
                })
                continue

            # Extract text from PDF
            raw_text = _extract_pdf_text(contents).strip()
            if not raw_text:
                results.append({
                    "file_name": filename,
                    "status": "error",
                    "reason": "no text extracted",
                })
                continue

            processed = process_resume_text(
                raw_text=raw_text,
                source_url=source_url,
                file_name=filename,
            )
            resume_id = processed["resume_id"]
            parsed = processed["parsed"]

            results.append({
                "file_name": filename,
                "status": "ok",
                "resume_id": resume_id,
                "candidate_name": parsed.get("candidate_name"),
                "current_title": parsed.get("current_title"),
            })

        except Exception as e:
            results.append({
                "file_name": filename,
                "status": "error",
                "reason": str(e),
            })

    return {
        "count": len(results),
        "items": results,
    }



    


@app.post("/match/top-by-role")
async def get_top_matches_by_role(
    role_name: str = Form(...),
    top_k: int = Form(3),
):
    """
    Input from UI:
      - role_name (e.g. 'Senior Data Scientist')
      - top_k (3 or 5)

    Backend:
      - finds latest JD with that role in memories (type='job')
      - computes vector similarity with all resumes
      - returns top-K resumes with ATS score + file_name + candidate_name.
    """
    # If top_k is very large (e.g. 1000), it effectively returns "all"
    try:
        matches = get_top_matches_for_role(role_name=role_name, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error (match/top-by-role): {e}")

    return {
        "role_name": role_name,
        "top_k": top_k,
        "matches": matches,
    }


@app.post("/match/top-by-jd")
async def get_top_matches_by_jd_id(
    jd_id: str = Form(...),
    top_k: int = Form(3),
):
    """
    Input from UI:
      - jd_id: database UUID of the uploaded JD
      - top_k (3, 5, or 10)

    Backend:
      - uses the JD's embedding directly from the database
      - computes vector similarity with all resumes
      - returns top-K resumes with ATS score + file_name + candidate_name.
    """
    try:
        from ranking import get_top_k_resumes_for_jd_memory
        matches = get_top_k_resumes_for_jd_memory(jd_memory_id=jd_id, top_k=top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error (match/top-by-jd): {e}")

    return {
        "jd_id": jd_id,
        "top_k": top_k,
        "matches": matches,
    }


@app.post("/send-emails")
async def send_emails_to_candidates(
    jd_id: str = Form(...),
    candidate_ids: List[str] = Form(...),
):
    """
    Send personalized emails to selected candidates.
    
    Args:
        jd_id: Database UUID of the JD
        candidate_ids: List of resume IDs to send emails to
    
    Returns:
        Summary of sent emails with success/failure status
    """
    from db import get_connection
    from mailing_agent import generate_personalized_email
    from email_sender import send_email
    import uuid
    
    results = []
    conn = get_connection()
    
    try:
        # Fetch JD details including embedding
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, canonical_json, embedding FROM memories WHERE id = %s",
            [jd_id]
        )
        jd_row = cur.fetchone()
        
        if not jd_row:
            raise HTTPException(status_code=404, detail=f"JD not found: {jd_id}")
        
        jd_data = {
            "id": jd_row[0],
            "title": jd_row[1],
            "canonical_json": jd_row[2],
            "role": jd_row[2].get("role") if jd_row[2] else "Position",
            "embedding": jd_row[3] # Get the JD embedding
        }
        
        # Process each candidate
        for idx, resume_id in enumerate(candidate_ids, start=1):
            try:
                # Fetch resume details AND calculate similarity on the fly
                # We use the JD embedding literal for the distance calculation
                jd_embedding_literal = jd_data["embedding"]
                
                cur.execute(
                    """
                    SELECT 
                        id, 
                        candidate_name, 
                        email, 
                        canonical_json, 
                        metadata, 
                        embedding,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM resumes 
                    WHERE id = %s
                    """,
                    [jd_embedding_literal, resume_id]
                )
                resume_row = cur.fetchone()
                
                if not resume_row:
                    results.append({
                        "resume_id": resume_id,
                        "status": "error",
                        "message": "Resume not found"
                    })
                    continue
                
                similarity = float(resume_row[6])
                ats_score = int(max(0.0, min(1.0, similarity)) * 100)
                
                candidate_data = {
                    "id": resume_row[0],
                    "candidate_name": resume_row[1],
                    "email": resume_row[2],
                    "canonical_json": resume_row[3],
                    "metadata": resume_row[4],
                    "embedding": resume_row[5]
                }
                
                candidate_email = candidate_data.get("email")
                if not candidate_email:
                    results.append({
                        "resume_id": resume_id,
                        "candidate_name": candidate_data.get("candidate_name"),
                        "status": "error",
                        "message": "No email address found"
                    })
                    continue
                
                # Create outreach record
                outreach_id = str(uuid.uuid4())
                
                # Generate personalized email
                email_content = generate_personalized_email(
                    candidate_data=candidate_data,
                    jd_data=jd_data,
                    outreach_id=outreach_id,
                    rank=idx,
                    ats_score=ats_score 
                )
                
                # Send email
                send_result = send_email(
                    to_email=candidate_email,
                    subject=email_content["subject"],
                    html_body=email_content["body"]
                )
                
                if send_result["success"]:
                    # Store in database with embedding and REAL ATS score
                    embedding_literal = candidate_data.get("embedding")
                    
                    cur.execute(
                        """
                        INSERT INTO candidate_outreach 
                        (id, resume_id, jd_id, candidate_email, candidate_name, 
                         email_subject, email_body, embedding, rank, ats_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, %s, %s)
                        """,
                        [
                            outreach_id,
                            resume_id,
                            jd_id,
                            candidate_email,
                            candidate_data.get("candidate_name"),
                            email_content["subject"],
                            email_content["body"],
                            embedding_literal,
                            idx,
                            ats_score
                        ]
                    )
                    conn.commit()
                    
                    results.append({
                        "resume_id": resume_id,
                        "candidate_name": candidate_data.get("candidate_name"),
                        "email": candidate_email,
                        "status": "success",
                        "message": "Email sent successfully",
                        "ats_score": ats_score
                    })
                else:
                    results.append({
                        "resume_id": resume_id,
                        "candidate_name": candidate_data.get("candidate_name"),
                        "email": candidate_email,
                        "status": "error",
                        "message": send_result["message"]
                    })
                    
            except Exception as e:
                results.append({
                    "resume_id": resume_id,
                    "status": "error",
                    "message": str(e)
                })
        
        cur.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending emails: {str(e)}")
    finally:
        conn.close()    
    return {
        "total": len(candidate_ids),
        "sent": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results
    }


@app.get("/acknowledge/{outreach_id}")
async def acknowledge_interest(outreach_id: str, response: str):
    """
    Record candidate's acknowledgement (interested/not_interested).
    
    Args:
        outreach_id: UUID of the outreach record
        response: 'interested' or 'not_interested'
    
    Returns:
        HTML confirmation page
    """
    from db import get_connection
    from fastapi.responses import HTMLResponse
    
    if response not in ['interested', 'not_interested']:
        raise HTTPException(status_code=400, detail="Invalid response")
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Update acknowledgement and get JD info
        cur.execute(
            """
            UPDATE candidate_outreach 
            SET acknowledgement = %s, acknowledged_at = NOW(), updated_at = NOW()
            WHERE id = %s
            RETURNING candidate_name, jd_id
            """,
            [response, outreach_id]
        )
        
        row = cur.fetchone()
        conn.commit()
        cur.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Outreach record not found")
        
        candidate_name = row[0] or "Candidate"
        jd_id = row[1]
        
        # Automatically schedule interview if candidate is interested
        if response == 'interested':
            try:
                from interview_scheduler import schedule_interview_for_single_candidate
                
                # Schedule for the first available date (automatically finds it)
                print(f"[DEBUG] Attempting to schedule interview for outreach_id={outreach_id}")
                schedule_result = schedule_interview_for_single_candidate(
                    outreach_id=outreach_id,
                    num_slots=3
                )
                
                print(f"[DEBUG] Schedule result: {schedule_result}")
                
                # Check if scheduling was successful
                if schedule_result.get('success'):
                    interview_date = schedule_result.get('interview_date')
                    message = f"Thank you, {candidate_name}! We've sent you an interview invitation email for {interview_date}. Please check your inbox and select your preferred time slot."
                elif 'error' in schedule_result:
                    # Error occurred during scheduling
                    print(f"[ERROR] Scheduling error: {schedule_result.get('error')}")
                    message = f"Thank you, {candidate_name}! We've recorded your interest and our team will contact you soon."
                elif 'message' in schedule_result:
                    # Already scheduled
                    message = f"Thank you, {candidate_name}! {schedule_result['message']}"
                else:
                    print(f"[WARNING] Unexpected schedule result format: {schedule_result}")
                    message = f"Thank you, {candidate_name}! We've recorded your interest and our team will contact you soon."
                    
            except Exception as e:
                # If scheduling fails, still acknowledge but don't show error to candidate
                print(f"[EXCEPTION] Auto-scheduling failed: {e}")
                import traceback
                traceback.print_exc()
                message = f"Thank you, {candidate_name}! We've recorded your interest and our team will contact you soon."
            
            color = "#10b981"
        else:
            message = f"Thank you for your response, {candidate_name}. We appreciate your time."
            color = "#6b7280"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Response Recorded - Tek Leaders</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background-color: #f3f4f6;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 500px;
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: {color};
            margin-bottom: 20px;
        }}
        p {{
            color: #6b7280;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">{'✓' if response == 'interested' else '✗'}</div>
        <h1>Response Recorded</h1>
        <p>{message}</p>
    </div>
</body>
</html>
"""
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording acknowledgement: {str(e)}")
    finally:
        conn.close()


@app.get("/confirm-interview/{interview_id}")
async def confirm_interview(interview_id: str, slot: str, outreach_id: str | None = None):
    """
    Confirm a candidate's selected interview time slot.
    Automatically creates a Google Calendar event and sends final emails.
    
    Args:
        interview_id: UUID of the interview
        slot: Selected slot ID (slot1, slot2, or slot3)
        outreach_id: Optional authorization token
    
    Returns:
        HTML confirmation page with Meet link and event details
    """
    from interview_scheduler import confirm_interview_slot
    from fastapi.responses import HTMLResponse
    
    try:
        result = confirm_interview_slot(interview_id, slot, outreach_id)
        
        if "error" in result:
            # Log error for debugging
            import sys
            print(f"[ERROR] Interview confirmation failed: {result['error']}", file=sys.stderr)
            message = result["error"]
            color = "#dc3545"
            icon = "❌"
            meet_link = None
            event_link = None
        else:
            meet_link = result.get("meet_link")
            event_link = result.get("event_link")
            message = f"Your interview has been confirmed! Check your email for the Google Meet link and calendar invitation."
            color = "#28a745"
            icon = "✅"
        
        meet_html = ""
        if meet_link:
            meet_html = f"""
            <div style="margin-top: 20px; padding: 20px; background-color: #e8f5e9; border-radius: 8px; border-left: 4px solid #4caf50;">
                <p style="color: #2e7d32; font-weight: bold;">📹 Google Meet Link:</p>
                <a href="{meet_link}" style="color: #4caf50; text-decoration: none; word-break: break-all;">{meet_link}</a>
            </div>
            """
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Interview Confirmation - Tek Leaders</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 600px;
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: {color};
            margin-bottom: 20px;
            font-size: 28px;
        }}
        p {{
            color: #333;
            line-height: 1.6;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">{icon}</div>
        <h1>Interview Confirmed</h1>
        <p>{message}</p>
        {meet_html}
    </div>
</body>
</html>
"""
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error confirming interview: {str(e)}")


@app.post("/schedule-interviews")
async def schedule_interviews(
    jd_id: str = Form(...),
    interview_date: str = Form(...)  # Format: YYYY-MM-DD
):
    """
    Schedule interviews for all interested candidates for a given JD.
    
    Args:
        jd_id: Database UUID of the JD
        interview_date: Date for interviews (YYYY-MM-DD format)
    
    Returns:
        Summary of scheduled interviews
    """
    from interview_scheduler import schedule_interviews_for_interested_candidates
    from datetime import datetime
    
    try:
        # Parse the date
        date_obj = datetime.strptime(interview_date, "%Y-%m-%d")
        
        # Schedule interviews
        result = schedule_interviews_for_interested_candidates(
            jd_id=jd_id,
            interview_date=date_obj,
            num_slots=3
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scheduling interviews: {str(e)}")


@app.get("/confirm-interview/{interview_id}")
async def confirm_interview(interview_id: str, slot: str, outreach_id: str | None = None):
    """
    Confirm a candidate's selected interview time slot.
    
    Args:
        interview_id: UUID of the interview
        slot: Selected slot ID (slot1, slot2, or slot3)
    
    Returns:
        HTML confirmation page
    """
    from interview_scheduler import confirm_interview_slot
    from fastapi.responses import HTMLResponse
    
    try:
        result = confirm_interview_slot(interview_id, slot, outreach_id)
        
        if "error" in result:
            message = result["error"]
            color = "#dc3545"
            icon = "❌"
        else:
            slot_info = result.get("slot", {})
            start_time = slot_info.get("start", "")
            message = f"Your interview has been confirmed for {start_time}. We look forward to meeting you!"
            color = "#28a745"
            icon = "✅"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Interview Confirmation - Tek Leaders</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: {color};
            margin-bottom: 20px;
        }}
        p {{
            color: #333;
            line-height: 1.6;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">{icon}</div>
        <h1>Interview Confirmation</h1>
        <p>{message}</p>
    </div>
</body>
</html>
"""
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error confirming interview: {str(e)}")


@app.get("/interviewer/response/{interview_id}")
async def interviewer_response(interview_id: str, action: str):
    """
    Handle interviewer's response to interview approval request.
    
    Args:
        interview_id: UUID of the interview
        action: 'approve' or 'reject'
    
    Returns:
        HTML response confirming the action
    """
    from interview_scheduler import approve_interview, process_reschedule_request
    from fastapi.responses import HTMLResponse
    from db import get_connection
    
    if action not in ['approve', 'reject']:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve' or 'reject'")
    
    try:
        if action == 'approve':
            # Approve the interview and create calendar event
            result = approve_interview(interview_id)
            
            if "error" in result:
                message = f"Error: {result['error']}"
                color = "#dc3545"
                icon = "❌"
            else:
                message = "Interview approved! Calendar invite has been sent to both you and the candidate."
                color = "#28a745"
                icon = "✅"
                
        else:  # action == 'reject'
            # Show reschedule form
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT r.candidate_name, m.title 
                    FROM interview_schedules i
                    JOIN resumes r ON r.id = i.resume_id
                    JOIN memories m ON m.id = i.jd_id
                    WHERE i.id = %s
                    """,
                    [interview_id]
                )
                row = cur.fetchone()
                cur.close()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Interview not found")
                    
                candidate_name, jd_title = row
                
                # Return reschedule form
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Reschedule Interview - Tek Leaders</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 90%;
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 24px;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
        }}
        label {{
            display: block;
            margin-top: 15px;
            margin-bottom: 5px;
            color: #333;
            font-weight: bold;
        }}
        input {{
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }}
        button {{
            width: 100%;
            padding: 12px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 20px;
        }}
        button:hover {{
            background-color: #45a049;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Reschedule Interview</h1>
        <p class="subtitle">Candidate: <strong>{candidate_name}</strong><br>Position: <strong>{jd_title}</strong></p>
        
        <form method="post" action="/interviewer/reschedule/{interview_id}">
            <label for="new_date">New Date:</label>
            <input type="date" id="new_date" name="new_date" required>
            
            <label for="new_time">New Time:</label>
            <input type="time" id="new_time" name="new_time" required>
            
            <button type="submit">Propose New Time</button>
        </form>
    </div>
</body>
</html>
"""
                return HTMLResponse(content=html_content)
                
            finally:
                conn.close()
        
        # For approve action, show confirmation
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Response Recorded - Tek Leaders</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: {color};
            margin-bottom: 20px;
            font-size: 28px;
        }}
        p {{
            color: #333;
            line-height: 1.6;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">{icon}</div>
        <h1>Response Recorded</h1>
        <p>{message}</p>
    </div>
</body>
</html>
"""
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing response: {str(e)}")


@app.post("/interviewer/reschedule/{interview_id}")
async def interviewer_reschedule(
    interview_id: str,
    new_date: str = Form(...),
    new_time: str = Form(...)
):
    """
    Process interviewer's reschedule request.
    
    Args:
        interview_id: UUID of the interview
        new_date: New proposed date (YYYY-MM-DD)
        new_time: New proposed time (HH:MM)
    
    Returns:
        HTML confirmation
    """
    from interview_scheduler import process_reschedule_request
    from fastapi.responses import HTMLResponse
    
    try:
        result = process_reschedule_request(interview_id, new_date, new_time)
        
        if "error" in result:
            message = f"Error: {result['error']}"
            color = "#dc3545"
            icon = "❌"
        else:
            message = "Reschedule request sent to candidate. They will receive an email with the new proposed time."
            color = "#28a745"
            icon = "✅"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Reschedule Sent - Tek Leaders</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: {color};
            margin-bottom: 20px;
            font-size: 28px;
        }}
        p {{
            color: #333;
            line-height: 1.6;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">{icon}</div>
        <h1>Reschedule Request Sent</h1>
        <p>{message}</p>
    </div>
</body>
</html>
"""
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing reschedule: {str(e)}")


@app.get("/candidate/accept-reschedule/{interview_id}")
async def candidate_accept_reschedule(interview_id: str):
    """
    Candidate accepts the interviewer's proposed reschedule time.
    This will approve the interview and create the calendar event.
    
    Args:
        interview_id: UUID of the interview
    
    Returns:
        HTML confirmation page
    """
    from interview_scheduler import approve_interview
    from fastapi.responses import HTMLResponse
    
    try:
        # Approve the rescheduled interview
        result = approve_interview(interview_id)
        
        if "error" in result:
            message = f"Error: {result['error']}"
            color = "#dc3545"
            icon = "❌"
        else:
            message = "Thank you for confirming! Calendar invite has been sent to your email. We look forward to meeting you!"
            color = "#28a745"
            icon = "✅"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Reschedule Confirmed - Tek Leaders</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
        }}
        .icon {{
            font-size: 64px;
            margin-bottom: 20px;
        }}
        h1 {{
            color: {color};
            margin-bottom: 20px;
            font-size: 28px;
        }}
        p {{
            color: #333;
            line-height: 1.6;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">{icon}</div>
        <h1>Interview Confirmed</h1>
        <p>{message}</p>
    </div>
</body>
</html>
"""
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accepting reschedule: {str(e)}")


@app.get("/candidate/decline-reschedule/{interview_id}")
async def candidate_decline_reschedule(interview_id: str):
    """
    Candidate declines the interviewer's proposed time and requests different options.
    This will generate new time slots and send them to the candidate.
    
    Args:
        interview_id: UUID of the interview
    
    Returns:
        HTML page with new time slot options
    """
    from db import get_connection
    from fastapi.responses import HTMLResponse
    from interview_scheduler import _fetch_time_slots
    from datetime import datetime, timedelta
    from config import BASE_URL, COMPANY_NAME
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Fetch interview details
        cur.execute(
            """
            SELECT i.interview_date, i.outreach_id, r.candidate_name, m.title, m.id
            FROM interview_schedules i
            JOIN resumes r ON r.id = i.resume_id
            JOIN memories m ON m.id = i.jd_id
            WHERE i.id = %s
            """,
            [interview_id]
        )
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        interview_date, outreach_id, candidate_name, jd_title, jd_id = row
        
        # Generate new time slots for the same date
        time_slots = _fetch_time_slots(interview_date, 3)
        
        # Generate HTML for slot options
        slots_html = ""
        for idx, slot in enumerate(time_slots, 1):
            start_time = slot['start_time'].strftime('%I:%M %p').lstrip('0')
            end_time = slot['end_time'].strftime('%I:%M %p').lstrip('0')
            slot_id = f"slot{idx}"
            
            confirm_url = f"{BASE_URL}/confirm-interview/{interview_id}?slot={slot_id}&outreach_id={outreach_id}"
            
            slots_html += f"""
                <div class="slot-option">
                    <strong>Option {idx}: {start_time} - {end_time}</strong><br>
                    <a href="{confirm_url}" class="slot-button">Select This Time</a>
                </div>
            """
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Select New Time - Tek Leaders</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            font-size: 24px;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
        }}
        .slot-option {{
            margin: 15px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #4CAF50;
            border-radius: 4px;
        }}
        .slot-button {{
            display: inline-block;
            padding: 12px 30px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin-top: 10px;
        }}
        .slot-button:hover {{
            background-color: #45a049;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Select Your Preferred Time</h1>
        <p class="subtitle">Hi {candidate_name}, please choose one of the following time slots for your {jd_title} interview on {interview_date.strftime('%A, %B %d, %Y')}:</p>
        
        {slots_html}
        
        <p style="margin-top: 30px; font-size: 14px; color: #666;">
            If none of these times work, please reply to the original email and we'll work with you to find a suitable time.
        </p>
    </div>
</body>
</html>
"""
        
        cur.close()
        conn.close()
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing decline: {str(e)}")


@app.get("/interviews/list")
async def get_interviews_list(jd_id: str = None):
    """
    Get status of all scheduled interviews, optionally filtered by JD.
    
    Args:
        jd_id: Optional JD ID to filter by
    
    Returns:
        List of scheduled interviews with their status
    """
    from db import get_connection
    
    conn = get_connection()
    
    try:
        cur = conn.cursor()
        
        if jd_id:
            query = """
                SELECT 
                    i.id,
                    i.interview_date,
                    i.status,
                    i.selected_slot,
                    i.confirmed_slot_time,
                    r.candidate_name,
                    r.email,
                    m.title as jd_title
                FROM interview_schedules i
                JOIN resumes r ON r.id = i.resume_id
                JOIN memories m ON m.id = i.jd_id
                WHERE i.jd_id = %s
                ORDER BY i.interview_date DESC, i.created_at DESC
            """
            cur.execute(query, [jd_id])
        else:
            query = """
                SELECT 
                    i.id,
                    i.interview_date,
                    i.status,
                    i.selected_slot,
                    i.confirmed_slot_time,
                    r.candidate_name,
                    r.email,
                    m.title as jd_title
                FROM interview_schedules i
                JOIN resumes r ON r.id = i.resume_id
                JOIN memories m ON m.id = i.jd_id
                ORDER BY i.interview_date DESC, i.created_at DESC
            """
            cur.execute(query)
        
        rows = cur.fetchall()
        cur.close()
        
        interviews = []
        for row in rows:
            interviews.append({
                "interview_id": row[0],
                "interview_date": str(row[1]),
                "status": row[2],
                "selected_slot": row[3],
                "confirmed_time": str(row[4]) if row[4] else None,
                "candidate_name": row[5],
                "candidate_email": row[6],
                "jd_title": row[7]
            })
        
        return {
            "total": len(interviews),
            "interviews": interviews
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching interviews: {str(e)}")
    finally:
        conn.close()


@app.get("/interviews/status")
async def get_interviews_status(
    jd_id: str | None = None,
    status: str | None = None,
    q: str | None = None,
    sort_by: str | None = "date",
    sort_order: str | None = "desc",
    decision: str | None = None,
):
    """
    HR dashboard: show all interviews/outreach in an HTML table with filters, search, and sorting.
    """
    from db import get_connection
    from config import INTERVIEWER_EMAIL, COMPANY_NAME
    from fastapi.responses import HTMLResponse
    import json

    print("DEBUG: Executing get_interviews_status") # VERIFICATION PRINT
    conn = get_connection()
    try:
        cur = conn.cursor()

        # Enhanced query that joins candidate_outreach, memories, and interview_schedules
        base_sql = """
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
        """

        conditions = []
        params = []

        if jd_id:
            conditions.append("m.id = %s")
            params.append(jd_id)

        # Search filter
        if q:
            search_clause = """
                (LOWER(co.candidate_name) LIKE LOWER(%s)
                 OR LOWER(co.candidate_email) LIKE LOWER(%s)
                 OR LOWER(m.title) LIKE LOWER(%s))
            """
            params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
            conditions.append(search_clause)

        # Status filter logic
        if status:
            s = status.lower()
            if s == "scheduled":
                conditions.append("i.status = 'scheduled'")
            elif s == "completed":
                conditions.append("i.status = 'completed'")
            elif s == "cancelled":
                conditions.append("i.status IN ('cancelled', 'declined')")
            elif s == "pending":
                conditions.append("(i.status IN ('pending', 'waiting_approval', 'pending_reschedule') OR i.id IS NULL)")

        # Decision filter logic (Round 1 Decision)
        if decision:
            d = decision.lower()
            if d == "selected":
                conditions.append("f.final_recommendation = 'Make Offer'")
            elif d == "rejected":
                conditions.append("f.final_recommendation = 'Not Selected'")
            elif d == "hold":
                conditions.append("f.final_recommendation = 'Hold'")
            elif d == "pending":
                conditions.append("f.final_recommendation IS NULL")

        where_sql = ""
        if conditions:
            where_sql = "WHERE " + " AND ".join(conditions)

        # Sorting logic
        order_clause = "ORDER BY co.created_at DESC"  # Default
        if sort_by == "date":
            if sort_order == "asc":
                order_clause = "ORDER BY COALESCE(i.confirmed_slot_time, i.interview_date, co.created_at) ASC"
            else:
                order_clause = "ORDER BY COALESCE(i.confirmed_slot_time, i.interview_date, co.created_at) DESC"
        elif sort_by == "jd_id":
            if sort_order == "asc":
                order_clause = "ORDER BY m.short_id ASC NULLS LAST, m.id ASC"
            else:
                order_clause = "ORDER BY m.short_id DESC NULLS LAST, m.id DESC"

        query = f"""{base_sql}
            {where_sql}
            {order_clause}
        """

        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        
        with open("debug_log.txt", "a") as f:
            f.write(f"Query returned {len(rows)} rows\n")

    except Exception as e:
        conn.close()
        with open("debug_log.txt", "a") as f:
            f.write(f"ERROR: {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"Error fetching interviews: {str(e)}")

    conn.close()

    # Build HTML table
    table_rows = ""
    all_interviews_data = {}
    
    try:
        for row in rows:
            (outreach_id, cand_name, cand_email, resume_id, jd_id_val, short_id, role, uploaded_by, 
             interview_id, interview_date, confirmed_time, interview_status, event_link, 
             meet_link, selected_slot, acknowledgement, feedback_form_link, feedback_sent_at, final_recommendation,
             interview_round, hr_round_scheduled, hr_interview_id, hr_decision) = row

            # Determine Display Status
            display_status = "Pending Interview Mail"
            status_class = "status-pending"
            
            if interview_status == 'scheduled':
                display_status = "Scheduled Interview"
                status_class = "status-scheduled"
            elif interview_status == 'completed':
                display_status = "Completed Interview"
                status_class = "status-completed"
            elif interview_status in ['cancelled', 'declined']:
                display_status = "Cancelled"
                status_class = "status-cancelled"
            elif interview_status == 'waiting_approval':
                display_status = "Waiting Approval"
                status_class = "status-warning"
            elif interview_status == 'pending_reschedule':
                display_status = "Reschedule Proposed"
                status_class = "status-warning"
            elif interview_status == 'pending':
                display_status = "Pending Slot Selection"
                status_class = "status-pending"
            elif acknowledgement == 'not_interested':
                display_status = "Candidate Declined"
                status_class = "status-cancelled"
            
            # Format Date/Time
            date_str = ""
            time_str = ""
            if confirmed_time:
                date_str = confirmed_time.strftime('%Y-%m-%d')
                time_str = confirmed_time.strftime('%I:%M %p')
            elif interview_date:
                date_str = str(interview_date)
                time_str = "Slot not confirmed"
                
            # Use short_id if available, otherwise show first 8 chars of UUID
            jd_display_id = short_id if short_id else (jd_id_val[:8] + "..." if jd_id_val else "N/A")

            # Prepare JSON for modal
            feedback_sent_str = feedback_sent_at.strftime('%Y-%m-%d %I:%M %p') if feedback_sent_at else 'Not sent yet'
            detail_dict = {
                'interview_id': str(interview_id) if interview_id else 'N/A',
                'candidate_name': str(cand_name) if cand_name else 'N/A',
                'candidate_email': str(cand_email) if cand_email else 'N/A',
                'role': str(role) if role else 'N/A',
                'uploaded_by': 'hiring',
                'interviewer_email': str(INTERVIEWER_EMAIL) if INTERVIEWER_EMAIL else 'N/A',
                'interview_date': str(date_str) if date_str else 'N/A',
                'interview_time': str(time_str) if time_str else 'N/A',
                'slot': str(selected_slot) if selected_slot else 'N/A',
                'meet_link': str(meet_link) if meet_link else 'N/A',
                'feedback_link': str(feedback_form_link) if feedback_form_link else 'N/A',
                'feedback_sent': str(feedback_sent_str),
                'interview_round': int(interview_round) if interview_round else 1,
                'hr_round_scheduled': bool(hr_round_scheduled),
                'hr_interview_id': str(hr_interview_id) if hr_interview_id else None,
                'hr_decision': str(hr_decision) if hr_decision else None
            }
            
            # Store in global data object
            all_interviews_data[str(outreach_id)] = detail_dict

            # Map final recommendation to display text
            decision_display = "-"
            decision_class = ""
            if final_recommendation == "Make Offer":
                decision_display = "Selected"
                decision_class = "status-scheduled"  # Green
            elif final_recommendation == "Not Selected":
                decision_display = "Rejected"
                decision_class = "status-cancelled"  # Red
            elif final_recommendation == "Hold":
                decision_display = "On Hold"
                decision_class = "status-warning"  # Yellow
            else:
                decision_display = "Pending"
                decision_class = "status-pending"  # Yellow
            
            # Map HR decision to display text
            hr_decision_display = "-"
            hr_decision_class = ""
            if hr_decision == "Hire":
                hr_decision_display = "Selected"
                hr_decision_class = "status-scheduled"  # Green
            elif hr_decision == "Reject":
                hr_decision_display = "Not Selected"
                hr_decision_class = "status-cancelled"  # Red
            elif hr_decision == "Hold":
                hr_decision_display = "On Hold"
                hr_decision_class = "status-warning"  # Yellow
            elif hr_decision:
                hr_decision_display = hr_decision
                hr_decision_class = "status-warning"  # Yellow
            else:
                hr_decision_display = "Pending"
                hr_decision_class = "status-pending"  # Yellow

            # Sanitize and Escape Data for HTML Table
            # Ensure no newlines in IDs that go into JS
            safe_outreach_id = str(outreach_id).strip()
            safe_jd_id_val = html.escape(str(jd_id_val)) if jd_id_val else ""
            safe_jd_display_id = html.escape(str(jd_display_id))
            safe_role = html.escape(str(role)) if role else ""
            safe_event_link = str(event_link).replace('"', '&quot;') if event_link else ""
            
            # Calendar Link
            cal_html = f'<a href="{safe_event_link}" target="_blank" class="btn-link">📅 Open</a>' if event_link else "-"

            table_rows += f"""
            <tr>
                <td>hiring</td>
                <td><span title="{safe_jd_id_val}">{safe_jd_display_id}</span></td>
                <td>{safe_role}</td>
                <td>{date_str} {time_str}</td>
                <td><span class="badge {status_class}">{display_status}</span></td>
                <td>{cal_html}</td>
                <td>
                    <button class="btn btn-small btn-primary view-details-trigger" data-id="{safe_outreach_id}">View Details</button>
                </td>
                <td><span class="badge {decision_class}">{decision_display}</span></td>
                <td><span class="badge {hr_decision_class}">{hr_decision_display}</span></td>
            </tr>
            """
    
    except Exception as e:
        with open("debug_log.txt", "a") as f:
            f.write(f"ERROR building table rows: {str(e)}\n")
        raise HTTPException(status_code=500, detail=f"Error building table: {str(e)}")

    # Convert interview data to JSON for JavaScript
    # Use ensure_ascii=True to avoid encoding issues and escape for safe HTML embedding
    # Also replace </script> to prevent breaking the HTML script tag
    interviews_data_json = json.dumps(all_interviews_data, ensure_ascii=True, default=str).replace("</", "<\\/")

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HR Dashboard</title>
    <link rel="stylesheet" href="/static/styles.css">
    <style>
        .badge {{ padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .status-pending {{ background-color: #ffeeba; color: #856404; }}
        .status-warning {{ background-color: #ffc107; color: #212529; }}
        .status-scheduled {{ background-color: #d4edda; color: #155724; }}
        .status-completed {{ background-color: #cce5ff; color: #004085; }}
        .status-cancelled {{ background-color: #f8d7da; color: #721c24; }}
        
        .modal {{ display: none; position: fixed; z-index: 10000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.4); }}
        .modal-content {{ background-color: #fefefe; margin: 15% auto; padding: 20px; border: 1px solid #888; width: 500px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
        .close {{ color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }}
        .close:hover {{ color: black; }}
        .detail-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
        .detail-label {{ font-weight: bold; color: #555; }}
        .header-actions {{ display: flex; gap: 10px; }}
    </style>
</head>
<body>
  <div class="container" style="max-width: 1200px;">
    <header style="display: flex; justify-content: space-between; align-items: center;">
      <div>
        <h1>HR Dashboard</h1>
        <p class="subtitle">Interview Management & Tracking</p>
      </div>
      <div class="header-actions">
        <a href="/" class="btn btn-outline">Back to Home</a>
        <a href="/interviews/status" class="btn btn-secondary">↻ Refresh</a>
      </div>
    </header>
    
    <div class="card">
      <form method="get" action="/interviews/status" style="display: flex; gap: 1rem; align-items: flex-end; margin-bottom: 1rem; flex-wrap: wrap;">
        <div>
          <label for="status">Filter by Status</label>
          <select name="status" id="status">
            <option value="">All Statuses</option>
            <option value="pending" {"selected" if (status or "").lower() == "pending" else ""}>Pending</option>
            <option value="scheduled" {"selected" if (status or "").lower() == "scheduled" else ""}>Scheduled</option>
            <option value="completed" {"selected" if (status or "").lower() == "completed" else ""}>Completed</option>
            <option value="cancelled" {"selected" if (status or "").lower() == "cancelled" else ""}>Cancelled</option>
          </select>
        </div>
        <div>
          <label for="decision">Technical Round Decision</label>
          <select name="decision" id="decision">
            <option value="">All Decisions</option>
            <option value="selected" {"selected" if (decision or "").lower() == "selected" else ""}>Selected</option>
            <option value="rejected" {"selected" if (decision or "").lower() == "rejected" else ""}>Rejected</option>
            <option value="hold" {"selected" if (decision or "").lower() == "hold" else ""}>On Hold</option>
            <option value="pending" {"selected" if (decision or "").lower() == "pending" else ""}>Pending</option>
          </select>
        </div>
        <div>
          <label for="sort_by">Sort By</label>
          <select name="sort_by" id="sort_by">
            <option value="date" {"selected" if (sort_by or "date") == "date" else ""}>Date</option>
            <option value="jd_id" {"selected" if (sort_by or "date") == "jd_id" else ""}>Job ID</option>
          </select>
        </div>
        <div>
          <label for="sort_order">Order</label>
          <select name="sort_order" id="sort_order">
            <option value="desc" {"selected" if (sort_order or "desc") == "desc" else ""}>Descending</option>
            <option value="asc" {"selected" if (sort_order or "desc") == "asc" else ""}>Ascending</option>
          </select>
        </div>
        <div style="flex-grow: 1;">
          <label for="q">Search</label>
          <input type="text" id="q" name="q" placeholder="Candidate Name, Email, or Role" value="{q or ''}" style="width: 100%;"/>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button type="submit" class="btn btn-primary">Apply Filters</button>
          <a href="/interviews/status" class="btn btn-outline">Clear</a>
        </div>
      </form>
      
      <table class="results-table">
        <thead>
          <tr>
            <th>Uploaded By</th>
            <th>JD ID</th>
            <th>Role</th>
            <th>Date & Time</th>
            <th>Status</th>
            <th>Calendar</th>
            <th>Actions</th>
            <th>Technical Round Decision</th>
            <th>HR Decision</th>
          </tr>
        </thead>
        <tbody>
          {table_rows or '<tr><td colspan="9" style="text-align:center; padding: 20px;">No records found matching your criteria.</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Details Modal -->
  <div id="detailsModal" class="modal">
    <div class="modal-content">
      <span class="close" onclick="closeModal()">&times;</span>
      <h2 style="margin-top: 0;">Interview Details</h2>
      <div id="modalBody">
        <!-- Content populated by JS -->
      </div>
    </div>
  </div>

  <script>
    // Global Error Handler to catch anything
    window.onerror = function(msg, url, line) {{
        alert("System Error: " + msg + "\\nLine: " + line);
        return false;
    }};

    console.log("HR Dashboard Script Loaded");
    
    // Interview data store
    const allInterviewsData = {interviews_data_json};
    console.log("Loaded interview data:", allInterviewsData);
    
    let currentInterviewData = null;

    // Event delegation for view details buttons
    document.addEventListener('click', function(e) {{
        if (e.target && e.target.classList.contains('view-details-trigger')) {{
            const outreachId = e.target.getAttribute('data-id');
            openModal(outreachId);
        }}
    }});

    function openModal(outreachId) {{
        try {{
            console.log("Opening modal for outreach ID:", outreachId);
            // Ensure ID is a string
            const safeId = String(outreachId).trim();
            const data = allInterviewsData[safeId];
            
            if (!data) {{
                alert("No data found for this interview ID: " + safeId);
                console.error("No data for outreach ID:", safeId);
                console.log("Available IDs:", Object.keys(allInterviewsData));
                return;
            }}
            
            currentInterviewData = data;
            
            const modal = document.getElementById("detailsModal");
            const body = document.getElementById("modalBody");
            
            body.innerHTML = `
                <div class="detail-row"><span class="detail-label">Candidate Name:</span> <span>${{data.candidate_name}}</span></div>
                <div class="detail-row"><span class="detail-label">Candidate Email:</span> <span>${{data.candidate_email}}</span></div>
                <div class="detail-row"><span class="detail-label">Role:</span> <span>${{data.role}}</span></div>
                <div class="detail-row"><span class="detail-label">Uploaded By:</span> <span>${{data.uploaded_by}}</span></div>
                <hr>
                <div class="detail-row"><span class="detail-label">Interviewer:</span> <span>${{data.interviewer_email}}</span></div>
                <div class="detail-row"><span class="detail-label">Date:</span> <span>${{data.interview_date}}</span></div>
                <div class="detail-row"><span class="detail-label">Time:</span> <span>${{data.interview_time}}</span></div>
                <div class="detail-row"><span class="detail-label">Slot ID:</span> <span>${{data.slot}}</span></div>
                <div class="detail-row"><span class="detail-label">Meeting Link:</span> <span><a href="${{data.meet_link}}" target="_blank">${{data.meet_link}}</a></span></div>
                <hr>
                <div class="detail-row"><span class="detail-label">Feedback Sent:</span> <span style="color: ${{data.feedback_sent === 'Not sent yet' ? '#dc3545' : '#28a745'}};">${{data.feedback_sent}}</span></div>
                <hr>
                <div style="text-align: center; margin-top: 15px;">
                    <button class="btn btn-primary" onclick="viewTechnicalFeedback('${{data.interview_id}}')" style="margin-right: 10px;">📋 View Technical Feedback</button>
                    ${{data.hr_interview_id ? `<button class="btn btn-primary" onclick="viewHrFeedback('${{data.hr_interview_id}}')" style="margin-right: 10px;">📋 View HR Feedback</button>` : ''}}
                    <button class="btn btn-outline" onclick="closeModal()">Close</button>
                </div>
                <div id="feedbackSection" style="margin-top: 20px; display: none;">
                    <h3>Interview Feedback</h3>
                    <div id="feedbackContent"></div>
                </div>
            `;
            
            modal.style.display = "block";
        }} catch (err) {{
            alert("Javascript Error: " + err.message);
            console.error(err);
        }}
    }}

    function closeModal() {{
        document.getElementById("detailsModal").style.display = "none";
        // Reset feedback section
        const feedbackSection = document.getElementById("feedbackSection");
        if (feedbackSection) {{
            feedbackSection.style.display = "none";
            feedbackSection.querySelector("#feedbackContent").innerHTML = "";
        }}
    }}

    async function viewTechnicalFeedback(interviewId) {{
        const feedbackSection = document.getElementById("feedbackSection");
        const feedbackContent = document.getElementById("feedbackContent");
        
        feedbackContent.innerHTML = '<p style="text-align: center; color: #666;">Loading feedback...</p>';
        feedbackSection.style.display = "block";
        
        try {{
            const response = await fetch(`/api/feedback/view/${{interviewId}}`);
            const data = await response.json();
            
            if (data.feedback) {{
                const f = data.feedback;
                // Render all rating fields
                let content = '<div style="background: #f9fafb; padding: 15px; border-radius: 8px;">';
                
                // Show all ratings if available (Technical Round)
                if (f.technical_skills !== undefined) {{
                    content += '<h4 style="margin-top: 0; color: #667eea;">Technical Assessment</h4>';
                    content += `<div class="detail-row"><span class="detail-label">Technical Skills:</span> <span>${{f.technical_skills}}/5</span></div>`;
                    content += `<div class="detail-row"><span class="detail-label">Education/Training:</span> <span>${{f.education_training}}/5</span></div>`;
                    content += `<div class="detail-row"><span class="detail-label">Work Experience:</span> <span>${{f.work_experience}}/5</span></div>`;
                    content += `<div class="detail-row"><span class="detail-label">Organizational Skills:</span> <span>${{f.organizational_skills}}/5</span></div>`;
                    content += `<div class="detail-row"><span class="detail-label">Communication:</span> <span>${{f.communication}}/5</span></div>`;
                    content += `<div class="detail-row"><span class="detail-label">Attitude:</span> <span>${{f.attitude}}/5</span></div>`;
                    content += `<div class="detail-row"><span class="detail-label">Overall Rating:</span> <span style="font-weight: bold; color: #667eea;">${{f.overall_rating}}/5</span></div>`;
                    content += '<hr>';
                }}
                
                // Show HR ratings if available (HR Round)
                if (f.communication_skills !== undefined) {{
                    content += '<h4 style="margin-top: 10px; color: #667eea;">HR Assessment</h4>';
                    content += `<div class="detail-row"><span class="detail-label">Communication Skills:</span> <span>${{f.communication_skills}}/5</span></div>`;
                    content += `<div class="detail-row"><span class="detail-label">Problem Solving:</span> <span>${{f.problem_solving}}/5</span></div>`;
                    content += `<div class="detail-row"><span class="detail-label">Teamwork:</span> <span>${{f.teamwork}}/5</span></div>`;
                    content += `<div class="detail-row"><span class="detail-label">Leadership:</span> <span>${{f.leadership}}/5</span></div>`;
                    content += `<div class="detail-row"><span class="detail-label">Cultural Fit:</span> <span>${{f.cultural_fit}}/5</span></div>`;
                    if (f.current_ctc) {{
                        content += '<hr>';
                        content += '<h4 style="margin-top: 10px; color: #667eea;">Compensation Details</h4>';
                        content += `<div class="detail-row"><span class="detail-label">Current CTC:</span> <span>${{f.current_ctc}}</span></div>`;
                        content += `<div class="detail-row"><span class="detail-label">Expected CTC:</span> <span>${{f.expected_ctc}}</span></div>`;
                        content += `<div class="detail-row"><span class="detail-label">Notice Period:</span> <span>${{f.notice_period}}</span></div>`;
                    }}
                    content += '<hr>';
                }}
                
                // Show recommendation
                const rec = f.final_recommendation || f.recommendation; 
                content += `<div class="detail-row"><span class="detail-label">Recommendation:</span> <span style="font-weight: bold; font-size: 16px; color: ${{rec === 'Make Offer' || rec === 'Strong Hire' || rec === 'Hire' ? '#28a745' : rec === 'Not Selected' || rec === 'Do Not Hire' ? '#dc3545' : '#ffc107'}};">${{rec}}</span></div>`;
                content += `<div style="margin-top: 10px;"><strong>Comments:</strong><p style="padding: 10px; background: white; border-radius: 4px;">${{f.comments || f.additional_comments || 'No comments'}}</p></div>`;
                
                content += '</div>';
                feedbackContent.innerHTML = content;
                
                // ACTION BUTTONS Logic
                const interviewRound = currentInterviewData.interview_round;
                const hrScheduled = currentInterviewData.hr_round_scheduled;
                
                if (interviewRound == 1 && rec === 'Make Offer') {{
                    if (hrScheduled) {{
                        feedbackContent.innerHTML += `<div style="margin-top: 20px; text-align: center;"><button class="btn" disabled style="background:#28a745; opacity: 0.7; color:white;">✅ HR Round Scheduled</button></div>`;
                    }} else {{
                        feedbackContent.innerHTML += `
                            <div style="margin-top: 25px; padding-top: 20px; border-top: 2px solid #e5e7eb; text-align: center;">
                                <p><strong>Candidate passed Technical Round.</strong></p>
                                <button id="scheduleHrBtn-${{interviewId}}" class="btn" style="background-color: #667eea; color: white;" onclick="scheduleHrRound('${{interviewId}}')">
                                    📅 Schedule HR Round
                                </button>
                                <p id="hrStatus-${{interviewId}}"></p>
                            </div>
                        `;
                    }}
                }} else if (interviewRound == 2 && (rec === 'Strong Hire' || rec === 'Hire')) {{
                     feedbackContent.innerHTML += `
                        <div style="margin-top: 25px; text-align: center;">
                            <button id="proceedBtn-${{interviewId}}" class="btn" style="background-color: #28a745; color: white;" onclick="sendHrDecision('${{interviewId}}')">
                                ✉️ Send Offer Email
                            </button>
                            <p id="emailStatus-${{interviewId}}"></p>
                        </div>
                    `;
                }} else if (rec === 'Not Selected' || rec === 'Do Not Hire') {{
                    feedbackContent.innerHTML += `
                        <div style="margin-top: 25px; text-align: center;">
                            <button id="rejectBtn-${{interviewId}}" class="btn" style="background-color: #dc3545; color: white;" onclick="sendRejection('${{interviewId}}')">
                                ✉️ Send Rejection Email
                            </button>
                             <p id="rejectStatus-${{interviewId}}"></p>
                        </div>
                    `;
                }}
            }} else {{
                feedbackContent.innerHTML = '<p style="text-align: center; color: #999;">📭 No feedback submitted yet for this interview.</p>';
            }}
        }} catch (error) {{
            console.error('Error fetching feedback:', error);
            feedbackContent.innerHTML = '<p style="text-align: center; color: #dc3545;">❌ Error loading feedback.</p>';
        }}
    }}

    async function viewHrFeedback(hrInterviewId) {{
        const feedbackSection = document.getElementById("feedbackSection");
        const feedbackContent = document.getElementById("feedbackContent");
        
        feedbackContent.innerHTML = '<p style="text-align: center; color: #666;">Loading HR feedback...</p>';
        feedbackSection.style.display = "block";
        
        try {{
            const response = await fetch(`/api/feedback/view/${{hrInterviewId}}`);
            const data = await response.json();
            
            if (data.feedback) {{
                const f = data.feedback;
                
                // Parse HR-specific data from comments field
                const comments = f.additional_comments || f.comments || '';
                const parseField = (fieldName) => {{
                    const regex = new RegExp(`${{fieldName}}:\\s*(.+?)(?=\\n|$)`, 'i');
                    const match = comments.match(regex);
                    return match ? match[1].trim() : 'N/A';
                }};
                
                // Render all HR rating fields
                let content = '<div style="background: #f9fafb; padding: 15px; border-radius: 8px;">';
                
                // Show HR-specific information
                content += '<h4 style="margin-top: 0; color: #667eea;">HR Assessment Details</h4>';
                content += `<div class="detail-row"><span class="detail-label">Reason for Leaving:</span> <span>${{parseField('Reason for leaving')}}</span></div>`;
                content += `<div class="detail-row"><span class="detail-label">Previous Package:</span> <span>${{parseField('Previous Package')}}</span></div>`;
                content += `<div class="detail-row"><span class="detail-label">Offered Package:</span> <span>${{parseField('Offered Package')}}</span></div>`;
                content += `<div class="detail-row"><span class="detail-label">Expected Package:</span> <span>${{parseField('Expected Package')}}</span></div>`;
                content += `<div class="detail-row"><span class="detail-label">Notice Period:</span> <span>${{parseField('Notice Period')}}</span></div>`;
                content += `<div class="detail-row"><span class="detail-label">Date of Joining:</span> <span>${{parseField('Date of Joining')}}</span></div>`;
                
                content += '<hr>';
                content += '<h4 style="margin-top: 10px; color: #667eea;">Skills Rating</h4>';
                content += `<div class="detail-row"><span class="detail-label">Technical Skills:</span> <span>${{f.technical_skills}}/5</span></div>`;
                content += `<div class="detail-row"><span class="detail-label">Communication Skills:</span> <span>${{f.communication}}/5</span></div>`;
                content += `<div class="detail-row"><span class="detail-label">Teamwork:</span> <span>${{f.education_training}}/5</span></div>`;
                content += `<div class="detail-row"><span class="detail-label">Attitude:</span> <span>${{f.organizational_skills}}/5</span></div>`;
                content += `<div class="detail-row"><span class="detail-label">Time Management:</span> <span>${{f.work_experience}}/5</span></div>`;
                content += `<div class="detail-row"><span class="detail-label">Overall Impression:</span> <span>${{f.overall_rating}}/5</span></div>`;
                
                content += '<hr>';
                content += `<div class="detail-row"><span class="detail-label">Strengths:</span> <span>${{parseField('Strengths')}}</span></div>`;
                content += `<div class="detail-row"><span class="detail-label">Areas to Improve:</span> <span>${{parseField('Areas to Improve')}}</span></div>`;
                
                content += '<hr>';
                
                // Show recommendation
                const rec = f.final_recommendation || f.recommendation; 
                content += `<div class="detail-row"><span class="detail-label">Recommendation:</span> <span style="font-weight: bold; font-size: 16px; color: ${{rec === 'Hire' ? '#28a745' : rec === 'Reject' ? '#dc3545' : '#ffc107'}};">${{rec}}</span></div>`;
                
                const additionalComments = parseField('Additional Comments');
                if (additionalComments !== 'N/A') {{
                    content += `<div style="margin-top: 10px;"><strong>Additional Comments:</strong><p style="padding: 10px; background: white; border-radius: 4px;">${{additionalComments}}</p></div>`;
                }}
                
                content += '</div>';
                feedbackContent.innerHTML = content;
                
                // Add action buttons based on recommendation
                if (rec === 'Hire') {{
                    feedbackContent.innerHTML += `
                        <div style="margin-top: 25px; text-align: center;">
                            <button id="offerBtn-${{hrInterviewId}}" class="btn" style="background-color: #28a745; color: white;" onclick="sendHrDecision('${{hrInterviewId}}', 'offer')">
                                ✉️ Send Offer Email
                            </button>
                             <p id="offerStatus-${{hrInterviewId}}"></p>
                        </div>
                    `;
                }} else if (rec === 'Reject') {{
                    feedbackContent.innerHTML += `
                        <div style="margin-top: 25px; text-align: center;">
                            <button id="rejectBtn-${{hrInterviewId}}" class="btn" style="background-color: #dc3545; color: white;" onclick="sendRejection('${{hrInterviewId}}')">
                                ✉️ Send Rejection Email
                            </button>
                             <p id="rejectStatus-${{hrInterviewId}}"></p>
                        </div>
                    `;
                }}
            }} else {{
                feedbackContent.innerHTML = '<p style="text-align: center; color: #999;">📭 No HR feedback submitted yet for this interview.</p>';
            }}
        }} catch (error) {{
            console.error('Error fetching HR feedback:', error);
            feedbackContent.innerHTML = '<p style="text-align: center; color: #dc3545;">❌ Error loading HR feedback.</p>';
        }}
    }}

    async function scheduleHrRound(interviewId) {{
        const btn = document.getElementById(`scheduleHrBtn-${{interviewId}}`);
        const status = document.getElementById(`hrStatus-${{interviewId}}`);
        
        if (!confirm('Schedule HR Round for this candidate? This will send an invitation email.')) return;
        
        btn.disabled = true;
        btn.textContent = 'Scheduling...';
        
        try {{
            const response = await fetch('/api/recruit/schedule-hr-round', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ interview_id: interviewId }})
            }});
            const data = await response.json();
            
            if (data.success) {{
                status.textContent = '✅ ' + data.message;
                status.style.color = 'green';
                btn.textContent = 'Scheduled';
            }} else {{
                status.textContent = '❌ ' + (data.error || 'Failed');
                status.style.color = 'red';
                btn.disabled = false;
                btn.textContent = 'Retry Schedule';
            }}
        }} catch (e) {{
            status.textContent = '❌ Error: ' + e.message;
            btn.disabled = false;
        }}
    }}
    
    async function sendHrDecision(interviewId, type) {{
         // Determine button and status IDs based on context (HR view vs Technical view)
         let btnId = `proceedBtn-${{interviewId}}`;
         let statusId = `emailStatus-${{interviewId}}`;
         
         if (type === 'offer' || document.getElementById(`offerBtn-${{interviewId}}`)) {{
             btnId = `offerBtn-${{interviewId}}`;
             statusId = `offerStatus-${{interviewId}}`;
         }}
         
         const btn = document.getElementById(btnId);
         const status = document.getElementById(statusId);
         
         if (!btn) {{
             console.error("Button not found:", btnId);
             return;
         }}

         if (!confirm('Send Final Offer Email?')) return;
         
         btn.disabled = true;
         btn.textContent = 'Sending...';
         
         try {{
             const response = await fetch('/api/recruit/send-hr-decision', {{
                 method: 'POST',
                 headers: {{ 'Content-Type': 'application/json' }},
                 body: JSON.stringify({{ interview_id: interviewId }})
             }});
             const data = await response.json();
             if (data.success) {{
                 if (status) {{
                    status.textContent = '✅ ' + data.message;
                    status.style.color = 'green';
                 }}
                 btn.textContent = 'Sent';
             }} else {{
                 if (status) {{
                    status.textContent = '❌ ' + (data.error || 'Failed');
                    status.style.color = 'red';
                 }}
                 btn.disabled = false;
                 btn.textContent = 'Retry Send';
             }}
         }} catch (e) {{
             console.error(e);
             if (status) status.textContent = '❌ ' + e.message;
             btn.disabled = false;
         }}
    }}
    
    async function sendRejection(interviewId) {{
         const btn = document.getElementById(`rejectBtn-${{interviewId}}`);
         const status = document.getElementById(`rejectStatus-${{interviewId}}`);
         
         if (!confirm('Send Rejection Email?')) return;
         btn.disabled = true;
         
         try {{
            const response = await fetch('/api/send-decision-email', {{
                method: 'POST',
                 headers: {{ 'Content-Type': 'application/json' }},
                 body: JSON.stringify({{ interview_id: interviewId }})
            }});
            const data = await response.json();
             if (data.success) {{
                 if (status) {{
                     status.textContent = '✅ ' + data.message;
                     status.style.color = 'green';
                 }}
             }} else {{
                 if (status) {{
                     status.textContent = '❌ ' + (data.error || 'Failed');
                     status.style.color = 'red';
                 }}
             }}
         }} catch (e) {{
             console.error(e);
             if (status) status.textContent = '❌ ' + e.message;
             btn.disabled = false;
         }}
    }}
  </script>
</body>
</html>
    """


    return HTMLResponse(content=html_content)


# Start feedback scheduler when app initializes
# from feedback_scheduler import start_feedback_scheduler

# Temporarily disabled - uncomment after testing
# @app.on_event("startup")
# async def startup_event():
#     """Start background jobs when app starts."""
#     print("[STARTUP] Starting feedback scheduler...")
#     start_feedback_scheduler()
#     print("[STARTUP] Feedback scheduler started successfully")



# --- HR Round & Round 2 Logic ---

@app.post("/api/recruit/technical-decision")
async def api_technical_decision(request: Dict[str, Any]):
    """Update Technical Round (Round 1) decision."""
    from db import get_connection
    
    interview_id = request.get("interview_id")
    decision = request.get("decision") # Selected, Rejected, On Hold, etc.
    
    if not interview_id or not decision:
        return JSONResponse({"success": False, "error": "interview_id and decision are required"}, status_code=400)

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE interview_schedules 
            SET technical_decision = %s, technical_decision_sent_at = NOW(), updated_at = NOW()
            WHERE id = %s
        """, [decision, interview_id])
        conn.commit()
        return {"success": True, "message": f"Technical decision updated to {decision}"}
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    finally:
        conn.close()


@app.post("/api/recruit/schedule-hr-round")
async def api_schedule_hr_round(request: Dict[str, Any]):
    """Schedule HR Round (Round 2) for a candidate."""
    from interview_scheduler import schedule_hr_round_interview
    
    interview_id = request.get("interview_id") # Original Round 1 interview ID
    if not interview_id:
        return JSONResponse({"success": False, "error": "interview_id is required"}, status_code=400)
        
    return schedule_hr_round_interview(original_interview_id=interview_id)


@app.post("/api/hr-feedback/submit")
async def submit_hr_feedback(request: Dict[str, Any]):
    """Submit HR Round feedback."""
    from db import get_connection
    
    interview_id = request.get("interview_id")
    if not interview_id:
        return JSONResponse({"success": False, "error": "interview_id is required"}, status_code=400)
        
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Verify interview exists
        cur.execute("SELECT id FROM interview_schedules WHERE id = %s", [interview_id])
        if not cur.fetchone():
            return JSONResponse({"success": False, "error": "Interview not found"}, status_code=404)

        # Insert into hr_feedback
        fields = [
            'interview_id', 'candidate_name', 'job_title', 'interview_date', 'interviewer_name',
            'current_ctc', 'expected_ctc', 'company_ctc', 'reason_leave', 'notice_period', 'joining_date',
            'technical_skills', 'communication_skills', 'problem_solving', 'teamwork', 'leadership', 
            'domain_knowledge', 'adaptability', 'cultural_fit',
            'confidence', 'attitude', 'time_management', 'motivation', 'integrity',
            'clarity', 'examples_quality', 'job_understanding',
            'strengths', 'improvements', 'concerns',
            'recommendation', 'additional_comments'
        ]
        
        # Build query dynamically
        columns = ", ".join(fields)
        placeholders = ", ".join(["%s"] * len(fields))
        
        values = [request.get(f) for f in fields]
        
        # Handle empty strings for integer fields (convert to None/0)
        # Actually standard Postgres driver handles None as NULL, but empty string might be issue for integers
        # The frontend JS sends parsed ints, so should be fine. string fields can be empty strings.
        
        cur.execute(f"""
            INSERT INTO hr_feedback ({columns}, timestamp)
            VALUES ({placeholders}, NOW())
        """, values)
        
        conn.commit()
        return {"success": True, "message": "HR Feedback submitted successfully"}
        
    except Exception as e:
        conn.rollback()
        print(f"Error submitting HR feedback: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    finally:
        conn.close()


@app.post("/api/recruit/send-hr-decision")
async def send_hr_decision(request: Dict[str, Any]):
    """
    Send final decision email after HR Round.
    """
    from db import get_connection
    from candidate_decision_emails import generate_offer_email, generate_rejection_email
    from email_sender import send_email
    from config import COMPANY_NAME
    
    interview_id = request.get("interview_id")
    if not interview_id:
        return JSONResponse({"success": False, "error": "interview_id is required"}, status_code=400)
        
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # Get HR feedback recommendation and candidate info
        # We join with interview_schedules to get resume/memory info
        cur.execute("""
            SELECT 
                f.recommendation,
                r.candidate_name,
                r.email,
                m.title as jd_title
            FROM hr_feedback f
            JOIN interview_schedules i ON i.id = f.interview_id
            JOIN resumes r ON r.id = i.resume_id
            JOIN memories m ON m.id = i.jd_id
            WHERE f.interview_id = %s
            ORDER BY f.created_at DESC
            LIMIT 1
        """, [interview_id])
        
        row = cur.fetchone()
        
        if not row:
            return JSONResponse({"success": False, "error": "HR Feedback not found"}, status_code=404)
            
        recommendation, candidate_name, candidate_email, jd_title = row
        
        # Map recommendation to decision type
        # Options: Strong Hire, Hire, Neutral..., Do Not Hire
        is_offer = recommendation in ["Strong Hire", "Hire"]
        is_rejection = recommendation == "Do Not Hire"
        
        if not (is_offer or is_rejection):
            return JSONResponse({"success": False, "error": f"Recommendation '{recommendation}' does not trigger automatic email"}, status_code=400)
            
        # Generate Email
        if is_offer:
            # We use the standard offer email (which is final offer)
            email_content = generate_offer_email(candidate_name, jd_title, COMPANY_NAME)
            decision_status = "Offer Sent"
        else:
            email_content = generate_rejection_email(candidate_name, jd_title, COMPANY_NAME)
            decision_status = "Rejected"
            
        # Send Email
        send_result = send_email(
            to_email=candidate_email,
            subject=email_content["subject"],
            html_body=email_content["body"]
        )
        
        if send_result["success"]:
            # Update HR decision status
            cur.execute("""
                UPDATE interview_schedules 
                SET hr_decision = %s, hr_decision_sent_at = NOW()
                WHERE id = %s
            """, [decision_status, interview_id])
            conn.commit()
            return {"success": True, "message": f"Sent {decision_status} email to {candidate_name}"}
        else:
            return JSONResponse({"success": False, "error": "Failed to send email"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    finally:
        conn.close()


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
