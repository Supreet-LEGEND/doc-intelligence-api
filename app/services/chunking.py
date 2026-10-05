def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list:
    if not text or not text.strip():
        return []

    words = text.split()
    chunks = []

    if len(words) <= chunk_size:
        return [text.strip()]

    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]).strip())

        if end >= len(words):
            break

        start = max(end - chunk_overlap, 0)

    return chunks


def chunk_by_sentences(text: str, max_chunk_size: int = 500) -> list:
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks = []
    current = ""

    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks