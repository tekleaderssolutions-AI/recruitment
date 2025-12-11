# candidate_decision_emails.py
"""
Email templates for notifying candidates of interview decisions.
"""
from typing import Dict


def generate_offer_email(
    candidate_name: str,
    jd_title: str,
    company_name: str
) -> Dict[str, str]:
    """
    Generate email to notify candidate they've been selected.
    
    Args:
        candidate_name: Name of the candidate
        jd_title: Position/role title
        company_name: Company name
    
    Returns:
        Dictionary with 'subject' and 'body' keys
    """
    subject = f"Congratulations! Interview Decision - {jd_title}"
    
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
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 30px;
                border-radius: 8px 8px 0 0;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .content {{
                padding: 30px 20px;
            }}
            .icon {{
                font-size: 64px;
                text-align: center;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                font-size: 14px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Congratulations!</h1>
            </div>
            
            <div class="content">
                <div class="icon">✅</div>
                
                <p>Dear {candidate_name},</p>
                
                <p>Congratulations! You have successfully <strong>cleared the first round</strong> for the <strong>{jd_title}</strong> position at {company_name}.</p> <p>We were impressed with your performance and appreciate the effort you put into the interview.</p> <p>Our team will contact you shortly with details about the next round of the selection process.</p> <p>We wish you the very best for the upcoming stages!</p>
            </div>
            
            <div class="footer">
                <p>Best regards,<br><strong>{company_name} HR Team</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {
        "subject": subject,
        "body": body
    }


def generate_rejection_email(
    candidate_name: str,
    jd_title: str,
    company_name: str
) -> Dict[str, str]:
    """
    Generate email to notify candidate they were not selected.
    
    Args:
        candidate_name: Name of the candidate
        jd_title: Position/role title
        company_name: Company name
    
    Returns:
        Dictionary with 'subject' and 'body' keys
    """
    subject = f"Interview Decision - {jd_title}"
    
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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 8px 8px 0 0;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .content {{
                padding: 30px 20px;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                font-size: 14px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Interview Update</h1>
            </div>
            
            <div class="content">
                <p>Dear {candidate_name},</p>
                
                <p>Thank you for taking the time to interview with us for the <strong>{jd_title}</strong> position at {company_name}.</p>
                
                <p>After careful consideration, we regret to inform you that we will not be moving forward with your application at this time.</p>
                
                <p>We genuinely appreciate your interest in {company_name} and the effort you put into the interview process. We were impressed by your qualifications and encourage you to apply for future opportunities that match your skills and experience.</p>
                
                <p>We wish you the very best in your job search and future career endeavors.</p>
            </div>
            
            <div class="footer">
                <p>Best regards,<br><strong>{company_name} HR Team</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {
        "subject": subject,
        "body": body
    }
