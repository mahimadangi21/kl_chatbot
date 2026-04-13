import os
import pdfplumber
import json

def extract_knowledge():
    kb_path = "knowledge_base"
    
    knowledge_data = {}
    
    # Get all PDF/TXT/DOCX files from knowledge_base
    files = [f for f in os.listdir(kb_path) if f.lower().endswith(('.pdf', '.txt', '.docx'))]
    print(f"Found files: {files}")
    
    for filename in files:
        path = os.path.join(kb_path, filename)
        print(f"Extracting {filename}...")
        text = ""
        try:
            if filename.lower().endswith('.pdf'):
                with pdfplumber.open(path) as pdf:
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
            else:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            
            if text.strip():
                knowledge_data[filename] = text.strip()
                print(f"Successfully extracted {len(text)} characters from {filename}")
            else:
                print(f"Warning: No text extracted from {filename}")
        except Exception as e:
            print(f"Error extracting {filename}: {e}")
            
    # Write to a Python file
    output_path = "src/knowledge_data.py"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# This file is auto-generated. Do not edit manually.\n\n")
        f.write("KNOWLEDGE_BASE = {\n")
        for filename, text in knowledge_data.items():
            f.write(f"    {json.dumps(filename)}: {json.dumps(text)},\n")
        f.write("}\n")
    
    print(f"Knowledge base embedded into {output_path}")

if __name__ == "__main__":
    extract_knowledge()
