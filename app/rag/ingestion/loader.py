from PyPDF2 import PdfReader


def load_pdf_pages(file_path):
    reader = PdfReader(file_path)
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        pages.append({
            "page_number": page_number,
            "text": page.extract_text() or "",
        })

    return pages


def load_pdf(file_path):
    return "\n".join(page["text"] for page in load_pdf_pages(file_path))
