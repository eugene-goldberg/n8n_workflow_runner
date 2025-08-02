#!/usr/bin/env python3
"""Convert markdown reports to PDFs using a reliable method"""

import os
from pathlib import Path
from fpdf import FPDF
import re

class MarkdownToPDF(FPDF):
    """Custom PDF class for markdown conversion"""
    
    def __init__(self):
        super().__init__()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)
        
    def add_title(self, title):
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(5)
        
    def add_heading(self, text, level=1):
        sizes = {1: 14, 2: 12, 3: 11}
        self.set_font('Helvetica', 'B', sizes.get(level, 11))
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.set_font('Helvetica', '', 10)
        
    def add_paragraph(self, text):
        self.set_font('Helvetica', '', 10)
        # Handle bullet points
        if text.strip().startswith('- ') or text.strip().startswith('* '):
            self.cell(10, 5, '-')  # Use hyphen instead of bullet
            text = text.strip()[2:]
            self.multi_cell(0, 5, text)
        else:
            self.multi_cell(0, 5, text)
        self.ln(2)

def convert_markdown_to_pdf(md_file, pdf_file):
    """Convert a markdown file to PDF"""
    
    pdf = MarkdownToPDF()
    
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        
        if not line:
            pdf.ln(5)
            continue
            
        # Handle headers
        if line.startswith('# '):
            pdf.add_title(line[2:])
        elif line.startswith('## '):
            pdf.add_heading(line[3:], level=1)
        elif line.startswith('### '):
            pdf.add_heading(line[4:], level=2)
        elif line.startswith('#### '):
            pdf.add_heading(line[5:], level=3)
        # Handle bold text
        elif line.startswith('**') and line.endswith('**'):
            pdf.set_font('Helvetica', 'B', 10)
            pdf.add_paragraph(line[2:-2])
            pdf.set_font('Helvetica', '', 10)
        # Handle lists and regular text
        else:
            # Clean up markdown formatting
            line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)  # Remove bold markers
            line = re.sub(r'\*(.*?)\*', r'\1', line)      # Remove italic markers
            # Replace special characters
            line = line.replace('✓', '[OK]')
            line = line.replace('✗', '[X]')
            line = line.replace('⚠️', '[!]')
            line = line.replace('→', '->')
            line = line.replace('—', '--')
            line = line.replace('"', '"').replace('"', '"')
            line = line.replace(''', "'").replace(''', "'")
            pdf.add_paragraph(line)
    
    pdf.output(pdf_file)

def main():
    """Convert all markdown reports to PDFs"""
    
    data_dir = Path("data")
    reports = [
        ("Q1_2025_Customer_Analysis_Report.md", "Q1_2025_Customer_Analysis_Report.pdf"),
        ("Product_Development_Status_April_2025.md", "Product_Development_Status_April_2025.pdf"),
        ("Risk_Assessment_Financial_Report_2025.md", "Risk_Assessment_Financial_Report_2025.pdf")
    ]
    
    print("Converting SpyroSolutions reports to PDF format...")
    print("=" * 60)
    
    for md_name, pdf_name in reports:
        md_path = data_dir / md_name
        pdf_path = data_dir / pdf_name
        
        if not md_path.exists():
            print(f"✗ Source not found: {md_name}")
            continue
            
        try:
            convert_markdown_to_pdf(md_path, pdf_path)
            file_size = pdf_path.stat().st_size / 1024  # KB
            print(f"✓ Converted: {md_name} → {pdf_name} ({file_size:.1f} KB)")
        except Exception as e:
            print(f"✗ Failed to convert {md_name}: {e}")
    
    print("\n" + "=" * 60)
    print("PDF conversion complete!")
    print("\nReady for ingestion into the knowledge graph.")

if __name__ == "__main__":
    main()