"""
HR Decision Email Templates
Templates for congratulations and rejection emails
"""
from typing import Dict


def generate_congratulations_email(candidate_name: str, position: str, ctc: str, joining_date: str) -> Dict[str, str]:
    """
    Generate congratulations email for hired candidates.
    
    Args:
        candidate_name: Full name of the candidate
        position: Job position/title
        ctc: Total CTC package
        joining_date: Expected date of joining
    
    Returns:
        Dictionary with 'subject' and 'body' keys
    """
    subject = f"🎉 Congratulations! You're Selected for {position} at Tek Leaders"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
            .highlight {{ background: #f0f9ff; padding: 20px; border-left: 4px solid #667eea; margin: 20px 0; border-radius: 4px; }}
            .details {{ margin: 20px 0; }}
            .details-row {{ display: flex; padding: 10px 0; border-bottom: 1px solid #f3f4f6; }}
            .details-label {{ font-weight: bold; min-width: 150px; color: #667eea; }}
            .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; color: #6b7280; font-size: 14px; }}
            .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; font-size: 28px;">🎉 Congratulations!</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">You've Been Selected!</p>
            </div>
            
            <div class="content">
                <p>Dear <strong>{candidate_name}</strong>,</p>
                
                <div class="highlight">
                    <p style="margin: 0; font-size: 16px; color: #1f2937;">
                        <strong>We are thrilled to inform you that you have been selected for the position of {position} at Tek Leaders India Private Limited!</strong>
                    </p>
                </div>
                
                <p>After careful consideration of your interview performance and qualifications, we are pleased to extend this offer to you.</p>
                
                <div class="details">
                    <h3 style="color: #667eea; margin-bottom: 15px;">📋 Offer Details:</h3>
                    <div class="details-row">
                        <span class="details-label">Position:</span>
                        <span>{position}</span>
                    </div>
                    <div class="details-row">
                        <span class="details-label">Total CTC:</span>
                        <span><strong>{ctc}</strong> per annum</span>
                    </div>
                    <div class="details-row">
                        <span class="details-label">Expected Joining Date:</span>
                        <span><strong>{joining_date}</strong></span>
                    </div>
                </div>
                
                <p><strong>📎 Please find your official offer letter attached to this email.</strong></p>
                
                <p>The offer letter contains detailed information about:</p>
                <ul>
                    <li>Compensation breakdown</li>
                    <li>Probation period and terms</li>
                    <li>Notice period requirements</li>
                    <li>Employment terms and conditions</li>
                </ul>
                
                <p><strong>Next Steps:</strong></p>
                <ol>
                    <li>Review the attached offer letter carefully</li>
                    <li>Confirm your acceptance and joining date at the earliest</li>
                    <li>Reach out if you have any questions or need clarifications</li>
                </ol>
                
                <p>We are excited to welcome you to the Tek Leaders family and look forward to your valuable contributions to our organization!</p>
                
                <p style="margin-top: 30px;">
                    <strong>Warm Regards,</strong><br>
                    <strong>Anuradha K</strong><br>
                    Manager - Operations<br>
                    Tek Leaders India Private Limited<br>
                    📞 040-44627896
                </p>
            </div>
            
            <div class="footer">
                <p style="margin: 0;">
                    <strong>Tek Leaders India Private Limited</strong><br>
                    2nd Floor, Sarvotham, Plot No. 12, Deloitte Dr, Phase 2, Hitech City, Hyderabad - 81
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {
        "subject": subject,
        "body": body
    }


def generate_rejection_email(candidate_name: str, position: str) -> Dict[str, str]:
    """
    Generate rejection email for candidates not selected.
    
    Args:
        candidate_name: Full name of the candidate
        position: Job position/title they applied for
    
    Returns:
        Dictionary with 'subject' and 'body' keys
    """
    subject = f"Update on Your Application for {position} at Tek Leaders"
    
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #f3f4f6; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #ffffff; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
            .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; font-size: 24px; color: #1f2937;">Application Update</h1>
            </div>
            
            <div class="content">
                <p>Dear <strong>{candidate_name}</strong>,</p>
                
                <p>Thank you for taking the time to interview for the <strong>{position}</strong> position at Tek Leaders India Private Limited. We appreciate your interest in our company and the effort you put into the interview process.</p>
                
                <p>After careful consideration, we regret to inform you that we have decided to move forward with other candidates whose qualifications more closely match our current needs for this particular role.</p>
                
                <p>This decision was not easy, as we had many qualified candidates. Please know that this does not diminish your skills and experience. We were impressed by your background and encourage you to apply for future opportunities that align with your expertise.</p>
                
                <p>We will keep your resume on file and may reach out if a suitable position becomes available in the future.</p>
                
                <p>We wish you all the best in your job search and future professional endeavors.</p>
                
                <p style="margin-top: 30px;">
                    <strong>Best Regards,</strong><br>
                    <strong>HR Team</strong><br>
                    Tek Leaders India Private Limited<br>
                    📞 040-44627896
                </p>
            </div>
            
            <div class="footer">
                <p style="margin: 0;">
                    <strong>Tek Leaders India Private Limited</strong><br>
                    2nd Floor, Sarvotham, Plot No. 12, Deloitte Dr, Phase 2, Hitech City, Hyderabad - 81
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {
        "subject": subject,
        "body": body
    }
