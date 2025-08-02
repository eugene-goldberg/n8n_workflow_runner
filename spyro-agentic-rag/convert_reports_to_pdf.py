#!/usr/bin/env python3
"""Convert markdown reports to PDF format"""

import os
import sys
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
import markdown
from bs4 import BeautifulSoup
import re

def clean_text_for_pdf(text):
    """Clean text for PDF generation"""
    # Replace special characters
    replacements = {
        '→': '->', 
        '↑': '[UP]',
        '↓': '[DOWN]',
        '✓': '[OK]',
        '✅': '[OK]',
        '⚠️': '[!]',
        '❌': '[X]',
        '•': '*',
        '–': '-',
        '—': '--',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '…': '...'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def markdown_to_pdf(md_file, pdf_file):
    """Convert a markdown file to PDF"""
    print(f"Converting {md_file} to {pdf_file}")
    
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Clean content
    md_content = clean_text_for_pdf(md_content)
    
    # Convert markdown to HTML
    html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    # Parse HTML
    soup = BeautifulSoup(html, 'html.parser')
    
    # Create PDF
    doc = SimpleDocTemplate(pdf_file, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Process HTML elements
    for element in soup.children:
        if element.name == 'h1':
            elements.append(Paragraph(element.text, title_style))
            elements.append(Spacer(1, 12))
        
        elif element.name == 'h2':
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(element.text, styles['Heading2']))
            elements.append(Spacer(1, 12))
        
        elif element.name == 'h3':
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(element.text, styles['Heading3']))
            elements.append(Spacer(1, 6))
        
        elif element.name == 'h4':
            elements.append(Paragraph(element.text, styles['Heading4']))
            elements.append(Spacer(1, 6))
        
        elif element.name == 'p':
            # Check if it's a metadata line
            text = element.text.strip()
            if text.startswith('**') and text.endswith('**'):
                elements.append(Paragraph(text, styles['BodyText']))
            else:
                elements.append(Paragraph(text, styles['Justify']))
            elements.append(Spacer(1, 12))
        
        elif element.name == 'ul':
            for li in element.find_all('li'):
                text = f"* {li.text}"
                elements.append(Paragraph(text, styles['BodyText']))
            elements.append(Spacer(1, 12))
        
        elif element.name == 'ol':
            for i, li in enumerate(element.find_all('li'), 1):
                text = f"{i}. {li.text}"
                elements.append(Paragraph(text, styles['BodyText']))
            elements.append(Spacer(1, 12))
        
        elif element.name == 'table':
            # Extract table data
            data = []
            
            # Headers
            headers = []
            if element.find('thead'):
                for th in element.find('thead').find_all('th'):
                    headers.append(th.text)
                data.append(headers)
            
            # Rows
            if element.find('tbody'):
                for tr in element.find('tbody').find_all('tr'):
                    row = []
                    for td in tr.find_all('td'):
                        row.append(td.text)
                    data.append(row)
            
            if data:
                # Create table
                t = Table(data)
                
                # Add style
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ])
                t.setStyle(style)
                
                elements.append(t)
                elements.append(Spacer(1, 12))
        
        elif element.name == 'hr':
            elements.append(Spacer(1, 12))
            elements.append(Paragraph('-' * 80, styles['Normal']))
            elements.append(Spacer(1, 12))
    
    # Build PDF
    try:
        doc.build(elements)
        print(f"Successfully created {pdf_file}")
    except Exception as e:
        print(f"Error creating PDF: {e}")
        # Try simpler approach
        simple_pdf_conversion(md_file, pdf_file)

def simple_pdf_conversion(md_file, pdf_file):
    """Simpler PDF conversion as fallback"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    # Read content
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Clean lines
    lines = [clean_text_for_pdf(line.rstrip()) for line in lines]
    
    # Create PDF
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter
    
    y = height - 72  # Start 1 inch from top
    x = 72  # 1 inch margin
    
    for line in lines:
        if y < 72:  # New page if near bottom
            c.showPage()
            y = height - 72
        
        # Simple formatting
        if line.startswith('#'):
            c.setFont("Helvetica-Bold", 14 if line.startswith('##') else 18)
            line = line.lstrip('#').strip()
        else:
            c.setFont("Helvetica", 10)
        
        # Draw text
        c.drawString(x, y, line[:100])  # Truncate long lines
        y -= 15
    
    c.save()
    print(f"Created simplified PDF: {pdf_file}")

def main():
    """Convert all markdown reports to PDF"""
    
    # Create PDFs directory
    pdf_dir = Path("data/pdfs")
    pdf_dir.mkdir(exist_ok=True)
    
    # List of reports to convert
    reports = [
        "Regional_Cost_Analysis_Report.md",
        "Customer_Commitment_Tracking_Report.md",
        "Product_Operational_Health_Report.md",
        "Feature_Adoption_Metrics_Report.md"
    ]
    
    # Convert each report
    for report in reports:
        md_path = Path("data") / report
        pdf_path = pdf_dir / report.replace('.md', '.pdf')
        
        if md_path.exists():
            try:
                markdown_to_pdf(str(md_path), str(pdf_path))
            except Exception as e:
                print(f"Error converting {report}: {e}")
        else:
            print(f"Warning: {md_path} not found")
    
    print(f"\nPDF files created in: {pdf_dir}")
    print("\nNext steps:")
    print("1. Review the PDF files in data/pdfs/")
    print("2. Use the LlamaIndex pipeline to ingest these PDFs")
    print("3. Re-run the business questions test to verify improvements")

if __name__ == "__main__":
    # Install required packages if needed
    try:
        import markdown
        from bs4 import BeautifulSoup
        from reportlab.lib import colors
    except ImportError:
        print("Installing required packages...")
        os.system("pip install markdown beautifulsoup4 reportlab")
        print("Please run the script again.")
        sys.exit(1)
    
    main()