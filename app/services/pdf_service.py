import fitz


def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += page.get_text()
    
    doc.close()
    return text


def extract_text_with_metadata(file_path: str) -> list:
    doc = fitz.open(file_path)
    pages = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        pages.append({
            "page_number": page_num + 1,
            "text": text,
            "char_count": len(text)
        })
    
    doc.close()
    return pages