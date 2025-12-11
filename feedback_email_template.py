# feedback_email_template.py
"""
Email template for requesting interviewer feedback after interviews.
"""
from typing import Dict


def generate_feedback_request_email(
    candidate_name: str,
    jd_title: str,
    interview_date: str,
    interview_time: str,
    yes_link: str,
    no_link: str,
    company_name: str
) -> Dict[str, str]:
    """
    Generate email to interviewer requesting confirmation if interview happened.
    
    Args:
        candidate_name: Name of the interviewed candidate
        jd_title: Position/role title
        interview_date: Date of the interview
        interview_time: Time of the interview
        yes_link: URL for "Yes, happened"
        no_link: URL for "No, not yet"
        company_name: Company name
    
    Returns:
        Dictionary with 'subject' and 'body' keys
    """
    subject = f"Action Required: Interview Status for {candidate_name}"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f5f5f5;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                padding: 30px;
                border-radius: 8px;
            }}
            .header {{
                background-color: #4CAF50;
                color: white;
                padding: 20px;
                border-radius: 8px 8px 0 0;
                text-align: center;
            }}
            h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .content {{
                padding: 20px 0;
                text-align: center;
            }}
            .interview-details {{
                margin: 20px 0;
                padding: 15px;
                background-color: #f8f9fa;
                border-left: 4px solid #4CAF50;
                border-radius: 4px;
                text-align: left;
            }}
            .detail-row {{
                margin: 8px 0;
            }}
            .detail-label {{
                font-weight: bold;
                color: #555;
            }}
            .button-container {{
                margin: 30px 0;
                text-align: center;
            }}
            .btn {{
                display: inline-block;
                padding: 15px 30px;
                margin: 10px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                color: white !important;
                transition: all 0.3s;
            }}
            .btn-yes {{
                background-color: #4CAF50;
            }}
            .btn-yes:hover {{
                background-color: #45a049;
            }}
            .btn-no {{
                background-color: #f44336;
            }}
            .btn-no:hover {{
                background-color: #d32f2f;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                font-size: 14px;
                color: #666;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 Interview Status Check</h1>
            </div>
            
            <div class="content">
                <p>Hi,</p>
                
                <p>We're checking in on the interview scheduled for today.</p>
                
                <div class="interview-details">
                    <div class="detail-row">
                        <span class="detail-label">Candidate:</span> {candidate_name}
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Position:</span> {jd_title}
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Interview Date:</span> {interview_date}
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Interview Time:</span> {interview_time}
                    </div>
                </div>
                
                <p><strong>Did this interview take place?</strong></p>
                
                <div class="button-container">
                    <a href="{yes_link}" class="btn btn-yes">✓ Yes, Interview Happening</a>
                    <a href="{no_link}" class="btn btn-no">✗ No, Interview Not Happening</a>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    If "Yes", you'll be directed to the feedback form.<br>
                    If "No", we'll note it in our records.
                </p>
            </div>
            
            <div class="footer">
                <p>Thank you for your time!</p>
                <p style="margin-top: 15px;">Best regards,<br><strong>{company_name} HR Team</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {
        "subject": subject,
        "body": body
    }
