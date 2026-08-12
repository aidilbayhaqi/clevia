from app.knowledge.chunking import normalize_text, semantic_chunks


def test_normalize_text_collapses_blank_lines():
    value = normalize_text("A\n\n\nB")
    assert value == "A\n\nB"


def test_semantic_chunks_preserve_content():
    source = "Paragraf pertama.\n\nParagraf kedua yang cukup pendek."
    chunks = semantic_chunks(source, max_chars=80)
    assert chunks
    assert "Paragraf pertama" in " ".join(chunks)
    assert "Paragraf kedua" in " ".join(chunks)
