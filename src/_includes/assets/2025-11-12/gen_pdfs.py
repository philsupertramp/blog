import os
import random
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import fitz

def convert_from_path(pdf_file):
    # Open the document
    doc = fitz.open(pdf_file)

    files = []
    # Iterate over the pages
    for page_num, page in enumerate(doc):
        # Define the zoom level (Matrix)
        # 2.0 = 2x zoom (roughly 144 dpi). Default is 72 dpi.
        mat = fitz.Matrix(2.0, 2.0) 
    
        # Render the page to an image (pixmap)
        pix = page.get_pixmap(matrix=mat)
    
        # Save the image
        pix.save(f"page-{page_num + 1}.png")
        files.append(f"page-{page_num + 1}.png")

    return files

OUTPUT_DIR = "test_files"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_invoice_pdf(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # 1. Header (Key-Value Extraction Test)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "INVOICE")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Invoice #: INV-{random.randint(1000, 9999)}")
    c.drawString(50, height - 100, "Date: 2023-10-27")
    c.drawString(400, height - 80, "Total Due:")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(470, height - 80, "$1,250.00") # Target for K/V extraction
    
    # 2. Table (Row Retrieval Test)
    data = [
        ['Item', 'Description', 'Qty', 'Price'],
        ['Widget A', 'High performance widget', '2', '$50.00'],
        ['Gadget B', 'Standard gadget', '5', '$20.00'],
        ['Service C', 'Consulting hours', '10', '$100.00'],
        ['Software D', 'License fee', '1', '$50.00']
    ]
    t = Table(data, colWidths=[100, 200, 50, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    t.wrapOn(c, width, height)
    t.drawOn(c, 50, height - 300)
    
    # 3. Tiny Text (Resolution Test)
    c.setFont("Helvetica", 4) # Very small text
    c.drawString(50, 30, "Reference Code: XJ9-TINY-TEXT-TEST-STRING-99")
    
    c.save()

def create_layout_pdf(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    # 1. Spatial Test (Shape vs Text)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "Figure A")
    
    # Draw a blue rectangle BELOW the text
    c.setFillColor(colors.blue)
    c.rect(100, height - 250, 100, 100, fill=1)
    
    # Draw a red circle TO THE RIGHT of the text
    c.setFillColor(colors.red)
    c.circle(400, height - 100, 40, fill=1)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 270, "The blue square is below 'Figure A'.")
    
    # 2. Entity List Test
    c.drawString(50, height - 400, "Participants: John Doe, Alice Smith, Bob Jones, Eve White.")
    
    # 3. Empty Area (Hallucination Test)
    # We leave the bottom half completely empty intentionally
    
    c.save()

def create_datasheet_pdf(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "Technical Datasheet: Model X")
    
    # Two Column Layout
    c.setFont("Helvetica", 10)
    left_text = "The Model X is designed for extreme environments. " * 5
    right_text = "Specifications include high thermal resistance. " * 5
    
    text_obj = c.beginText(50, height - 100)
    text_obj.textLines(left_text)
    c.drawText(text_obj)
    
    text_obj2 = c.beginText(300, height - 100)
    text_obj2.textLines(right_text)
    c.drawText(text_obj2)
    
    # Complex Table (Merged headers simulated)
    c.drawString(50, height - 300, "Performance Metrics")
    data = [
        ['Metric', 'Min', 'Max', 'Unit'],
        ['Voltage', '10', '24', 'V'],
        ['Current', '0.5', '2.0', 'A'],
        ['Temp', '-40', '85', 'C']
    ]
    t = Table(data)
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
    t.wrapOn(c, width, height)
    t.drawOn(c, 50, height - 400)

    c.save()

def generate_all():
    print("Generating test PDFs...")
    
    pdfs = [
        ("invoice_001.pdf", create_invoice_pdf),
        ("layout_test_001.pdf", create_layout_pdf),
        ("datasheet_001.pdf", create_datasheet_pdf)
    ]
    
    for name, func in pdfs:
        pdf_path = os.path.join(OUTPUT_DIR, name)
        func(pdf_path)
        print(f" -> Created {name}")


if __name__ == "__main__":
    generate_all()
