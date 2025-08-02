#!/usr/bin/env python3
"""Convert markdown reports to PDFs"""

import os
from pathlib import Path
import subprocess

def convert_md_to_pdf():
    """Convert markdown files to PDFs using pandoc or alternative method"""
    
    data_dir = Path("data")
    md_files = [
        "Q1_2025_Customer_Analysis_Report.md",
        "Product_Development_Status_April_2025.md", 
        "Risk_Assessment_Financial_Report_2025.md"
    ]
    
    print("Converting SpyroSolutions reports to PDF...")
    
    # Check if pandoc is available
    try:
        subprocess.run(["pandoc", "--version"], capture_output=True, check=True)
        has_pandoc = True
    except:
        has_pandoc = False
        print("Pandoc not found. Using alternative method...")
    
    for md_file in md_files:
        md_path = data_dir / md_file
        pdf_name = md_file.replace('.md', '.pdf')
        pdf_path = data_dir / pdf_name
        
        if has_pandoc:
            # Use pandoc for conversion
            try:
                subprocess.run([
                    "pandoc", str(md_path), 
                    "-o", str(pdf_path),
                    "--pdf-engine=xelatex",
                    "-V", "geometry:margin=1in",
                    "-V", "fontsize=11pt"
                ], check=True)
                print(f"✓ Converted {md_file} to {pdf_name}")
            except subprocess.CalledProcessError:
                # Try without xelatex
                try:
                    subprocess.run([
                        "pandoc", str(md_path), 
                        "-o", str(pdf_path)
                    ], check=True)
                    print(f"✓ Converted {md_file} to {pdf_name}")
                except:
                    print(f"✗ Failed to convert {md_file}")
        else:
            # Alternative: Use Python library
            try:
                from fpdf import FPDF
                
                # Read markdown content
                with open(md_path, 'r') as f:
                    content = f.read()
                
                # Create PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                
                # Simple conversion (limited formatting)
                for line in content.split('\n'):
                    if line.startswith('#'):
                        pdf.set_font("Arial", 'B', 14)
                        pdf.cell(0, 10, line.replace('#', '').strip(), ln=True)
                        pdf.set_font("Arial", size=10)
                    else:
                        pdf.multi_cell(0, 5, line)
                
                pdf.output(str(pdf_path))
                print(f"✓ Created simple PDF: {pdf_name}")
                
            except ImportError:
                print(f"✗ Cannot convert {md_file} - install fpdf2 or pandoc")
                # Keep markdown files for ingestion
                print(f"  Will use markdown file directly for ingestion")

if __name__ == "__main__":
    convert_md_to_pdf()
    
    print("\nSpyroSolutions reports ready for ingestion:")
    print("- Customer Analysis Report")
    print("- Product Development Status")  
    print("- Risk Assessment & Financial Report")
    print("\nThese reports contain rich entity and relationship data for knowledge graph extraction.")