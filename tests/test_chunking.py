import pytest

from app.services.text_processing import clean_text, chunk_text


def test_clean_text_normalizes_whitespace():
    text = "Hello   world!\r\n\r\nSecond paragraph."

    result = clean_text(text)

    assert result == "Hello world!\n\nSecond paragraph."


def test_chunk_text_returns_multiple_chunks():
    text = "document processing " * 200

    chunks = chunk_text(
        text,
        chunk_size=100,
        overlap=20,
    )

    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_chunk_text_empty_input():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [
        (0, 0),
        (100, -1),
        (100, 100),
        (100, 101),
    ],
)
def test_chunk_text_rejects_invalid_parameters(
    chunk_size,
    overlap,
):
    with pytest.raises(ValueError):
        chunk_text(
            "Some sample document text.",
            chunk_size=chunk_size,
            overlap=overlap,
        )
