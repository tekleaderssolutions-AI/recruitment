"""
Offer Letter PDF Generator
Generates professional offer letter PDFs for hired candidates
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime


def generate_offer_letter_pdf(candidate_name: str, position: str, ctc: str, joining_date: str, candidate_city: str = "Hyderabad") -> bytes:
    """
    Generate a 2-page offer letter PDF.
    
    Args:
        candidate_name: Full name of the candidate
        position: Job position/title
        ctc: Total CTC package (e.g., "12 LPA")
        joining_date: Expected date of joining
        candidate_city: Candidate's city (default: Hyderabad)
    
    Returns:
        PDF file as bytes
    """
    # Create PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor='black',
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor='black',
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor='black',
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=16
    )
    
    small_style = ParagraphStyle(
        'SmallText',
        parent=styles['Normal'],
        fontSize=9,
        textColor='black',
        alignment=TA_LEFT
    )
    
    # Company Header
    elements.append(Paragraph("PAN: AAFCT1424K", small_style))
    elements.append(Paragraph("TAN: HYDT06163D", small_style))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("<b>TEK LEADERS INDIA PRIVATE LTD</b>", header_style))
    elements.append(Paragraph("2<sup>nd</sup> Floor, Sarvotham, Plot No. 12, Deloitte Dr, Phase 2,", header_style))
    elements.append(Paragraph("Hitech City, Hyderabad -81, Ph: 040-44627896", header_style))
    elements.append(Spacer(1, 24))
    
    # Date
    today = datetime.now().strftime("%B %d, %Y")
    elements.append(Paragraph(f"<b>Dated:</b> {today}", body_style))
    elements.append(Spacer(1, 12))
    
    # Candidate Address
    elements.append(Paragraph(f"<b>{candidate_name}</b>", body_style))
    elements.append(Paragraph(candidate_city, body_style))
    elements.append(Spacer(1, 12))
    
    # Title
    elements.append(Paragraph("<b>Offer letter to join Tek Leaders India Private Limited Family!</b>", title_style))
    elements.append(Spacer(1, 12))
    
    # Greeting
    elements.append(Paragraph(f"Dear {candidate_name},", body_style))
    elements.append(Spacer(1, 6))
    
    # Body paragraphs
    para1 = f"""Thank you for exploring career opportunities with Tek Leaders India Private Limited. 
    Following our discussions, we are pleased to offer you the position of <b>{position}</b> at Tek Leaders India Private Limited."""
    elements.append(Paragraph(para1, body_style))
    
    para2 = f"""In this context, we shall offer you a Total CTC of <b>{ctc}</b> per annum, 
    you shall report to duty on <b>{joining_date}</b>. Annexure - 1 provides you with a break-up of the compensation package. 
    The compensation will be subject to statutory and other deductions as per company policies and practices."""
    elements.append(Paragraph(para2, body_style))
    
    para3 = """Please confirm on your date of joining at the earliest. A detailed letter of the 
    employment agreement will be issued on the day of your joining."""
    elements.append(Paragraph(para3, body_style))
    
    para4 = """You would be on probation for a period of three months and subject to your performance 
    during this period, the company will either confirm you, or extend your probation for a further period 
    of three or six months or will give you 15 days advance notice before being relieved from the organization."""
    elements.append(Paragraph(para4, body_style))
    
    para5 = """You must issue Three-month notice in writing to the company to terminate your employment 
    with the company and vice versa after completion of probation period."""
    elements.append(Paragraph(para5, body_style))
    
    para6 = """The company however reserves the right to terminate your services, if you are proved guilty 
    of gross misconduct, gross negligence, sexual harassment or if you have committed a fundamental breach 
    of contract and business ethics."""
    elements.append(Paragraph(para6, body_style))
    
    # Page break for page 2
    elements.append(PageBreak())
    
    # Page 2 content
    para7 = """You will not directly or indirectly engage in any business or serve, whether as principal, 
    partner, consultant, employee or contractor in any other capacity either full time or part time whatsoever 
    other than of the Company."""
    elements.append(Paragraph(para7, body_style))
    
    para8 = """You must not, at any time during your employment or after its termination, divulge to any 
    third party or otherwise make use of any trade secret or confidential information, which comes to your 
    knowledge during your employment relating to the business of the company. This might lead to strict legal action."""
    elements.append(Paragraph(para8, body_style))
    
    para9 = """We take this opportunity to welcome you as a part of our team and look forward to your 
    valuable contribution to the organization."""
    elements.append(Paragraph(para9, body_style))
    
    para10 = """Should you require any further clarifications, please feel free to contact us."""
    elements.append(Paragraph(para10, body_style))
    
    elements.append(Spacer(1, 24))
    
    # Signature
    elements.append(Paragraph("For Tek Leaders India Private Limited.", body_style))
    elements.append(Spacer(1, 36))
    elements.append(Paragraph("<b>Anuradha K</b>", body_style))
    elements.append(Paragraph("Manager - Operations", body_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


if __name__ == "__main__":
    # Test the PDF generation
    pdf = generate_offer_letter_pdf(
        candidate_name="Akshitha Chittireddy",
        position="AI Engineer (Trainee)",
        ctc="12 LPA",
        joining_date="January 15, 2025"
    )
    
    with open("test_offer_letter.pdf", "wb") as f:
        f.write(pdf)
    
    print("Test PDF generated: test_offer_letter.pdf")
