import pdfplumber
import sys

# Set stdout to utf-8 for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pdf_path = 'knowledge_base/mahima_dangi_contract.pdf'
with pdfplumber.open(pdf_path) as pdf:
    for i, page in enumerate(pdf.pages):
        print(f"--- PAGE {i+1} ---")
        print(page.extract_text())
