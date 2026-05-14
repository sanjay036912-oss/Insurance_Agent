import os
from extractor.pdf_extractor import extract_pdf_text


def extract_text(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Handle PDF
    if file_path.lower().endswith(".pdf"):
        return extract_pdf_text(file_path)

    # Handle TXT
    elif file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError("Unsupported file type. Use .txt or .pdf")

