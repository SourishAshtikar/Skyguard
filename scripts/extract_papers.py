#!/usr/bin/env python3
"""Extract text from all research papers for review."""
import os, sys
try:
    import fitz  # PyMuPDF
except ImportError:
    print("Installing pymupdf...")
    os.system("pip install pymupdf -q")
    import fitz

PAPERS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Research Papers")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "papers_text.txt")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
    for fname in sorted(os.listdir(PAPERS_DIR)):
        if not fname.endswith('.pdf'):
            continue
        fpath = os.path.join(PAPERS_DIR, fname)
        out.write(f"\n{'='*100}\n")
        out.write(f"PAPER: {fname}\n")
        out.write(f"{'='*100}\n\n")
        try:
            doc = fitz.open(fpath)
            for page_num, page in enumerate(doc):
                text = page.get_text()
                out.write(f"--- Page {page_num+1} ---\n")
                out.write(text)
                out.write("\n")
            doc.close()
        except Exception as e:
            out.write(f"[Error reading: {e}]\n")

print(f"Extracted text from all papers to: {OUTPUT_FILE}")
