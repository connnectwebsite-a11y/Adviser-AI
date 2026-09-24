import pymupdf


def extract_pdf_text(pdf_path):
    pages = []

    document = pymupdf.open(pdf_path)

    try:
        for page_number, page in enumerate(
            document,
            start=1
        ):
            text = page.get_text("text")

            pages.append({
                "page": page_number,
                "text": text
            })

    finally:
        document.close()

    return pages


def create_chunks(
    pages,
    chunk_size=180,
    overlap=40
):
    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than zero."
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative."
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size."
        )

    chunks = []

    for page in pages:
        if isinstance(page, dict):
            page_number = page.get("page")
            text = str(page.get("text", ""))
        else:
            page_number = None
            text = str(page)

        words = text.split()

        if not words:
            continue

        step = chunk_size - overlap

        for start in range(
            0,
            len(words),
            step
        ):
            end = start + chunk_size

            chunk_words = words[start:end]

            if not chunk_words:
                continue

            chunks.append({
                "page": page_number,
                "text": " ".join(chunk_words)
            })

            if end >= len(words):
                break

    return chunks
