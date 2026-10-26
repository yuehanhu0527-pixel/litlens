def chunk_text(
        text:str,
        chunk_size: int = 800,
        overlap: int = 100
) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)

        start = end - overlap
    return chunks 

def chunk_pages(
        pages:list[dict],
        chunk_size: int = 800,
        overlap:int = 100
)-> list[dict]:

    all_chunks = []

    for page in pages:
        page_number = page['page_number']
        text = page['text']

        text_chunks = chunk_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap
        )

        for chunk_index, chunk in enumerate(text_chunks):
            all_chunks.append({
                'page_number':page_number,
                'chunk_index':chunk_index,
                'text':chunk
            })
    return all_chunks

