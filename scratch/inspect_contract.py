import pdfplumber
import os

pdf_path = 'knowledge_base/mahima_dangi_contract.pdf'
if os.path.exists(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Read first two pages
        text = ""
        for i in range(min(len(pdf.pages), 2)):
            text += f"--- PAGE {i+1} ---\n"
            text += pdf.pages[i].extract_text() + "\n"
        print(text)
else:
    print(f"File not found: {pdf_path}")
