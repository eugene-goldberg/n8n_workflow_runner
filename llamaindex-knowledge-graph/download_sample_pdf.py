#!/usr/bin/env python3
"""Download a sample PDF for testing"""

import os
import requests
from pathlib import Path

def download_sample_pdf():
    """Download a sample PDF from arXiv"""
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Sample PDF URL (a popular machine learning paper)
    pdf_url = "https://arxiv.org/pdf/1706.03762.pdf"  # "Attention Is All You Need" paper
    pdf_name = "attention_is_all_you_need.pdf"
    pdf_path = data_dir / pdf_name
    
    if pdf_path.exists():
        print(f"PDF already exists: {pdf_path}")
        return str(pdf_path)
    
    print(f"Downloading sample PDF: {pdf_name}")
    print(f"From: {pdf_url}")
    
    try:
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()
        
        # Write PDF to file
        with open(pdf_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✓ Downloaded successfully to: {pdf_path}")
        print(f"  File size: {pdf_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Also create a simple sample PDF link
        with open(data_dir / "sample.pdf", 'wb') as f:
            f.write(pdf_path.read_bytes())
        
        return str(pdf_path)
        
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return None

if __name__ == "__main__":
    print("Sample PDF Downloader")
    print("=" * 50)
    
    pdf_path = download_sample_pdf()
    
    if pdf_path:
        print("\n✓ Sample PDF ready for testing!")
        print("\nYou can now run:")
        print("  python examples/simple_example.py")
        print("\nOr use the main pipeline:")
        print("  python examples/basic_usage.py")