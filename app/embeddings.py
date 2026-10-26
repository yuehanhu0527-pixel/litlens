from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text:str) -> list[float]:
    embedding = model.encode(text)
    return embedding.tolist()

def embed_chunks(chunks: list[dict]) -> list[dict]:
    embedded_chunks = []

    for chunk in chunks:
        embedding = embed_text(chunk['text'])

        embedded_chunks.append({
            'page_number':chunk['page_number'],
            'chunk_index':chunk['chunk_index'],
            'text':chunk['text'],
            'embedding':embedding

        })
    return embedded_chunks

