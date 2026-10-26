import pymupdf


def extract_pages_from_pdf(file_path: str) -> list[dict]:
    document = pymupdf.open(file_path)

    pages = []

    for page_index, page in enumerate(document):
        text = page.get_text("text")

        pages.append({
            "page_number": page_index + 1,
            "text": text
        })

    document.close()

    return pages