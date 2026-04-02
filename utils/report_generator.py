from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
import uuid

def generate_pdf_report(score, role, missing_skills="Not provided"):
    try:
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"report_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(reports_dir, filename)
        
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height - 80, "Skillora Career Report")
        
        c.setFont("Helvetica", 14)
        c.drawString(50, height - 120, f"Target Role: {role}")
        c.drawString(50, height - 150, f"ATS Score: {score}/100")
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 200, "Recommended Next Steps:")
        
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 230, "1. Focus on addressing any missing core skills.")
        c.drawString(50, height - 250, "2. Add specific, measurable results to your project descriptions.")
        c.drawString(50, height - 270, "3. Ensure your formatting is clean and easy for ATS parsers to read.")
        
        c.save()
        return filepath
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None
