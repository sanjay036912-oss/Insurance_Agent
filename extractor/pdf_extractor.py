import fitz  # PyMuPDF


def extract_pdf_text(file_path):
    text_parts = []

    doc = fitz.open(file_path)

    for page in doc:
        # 1. Regular page text (labels, static content)
        page_text = page.get_text()
        if page_text.strip():
            text_parts.append(page_text)

        # 2. Form field values (this was missing before)
        for widget in page.widgets():
            field_name = widget.field_name or ""
            field_value = widget.field_value or ""

            # Skip empty fields and checkbox states
            if not field_value or field_value in ("/Off", "/Yes", "Off", "Yes"):
                continue

            text_parts.append(f"{field_name}: {field_value}")

    return "\n".join(text_parts)