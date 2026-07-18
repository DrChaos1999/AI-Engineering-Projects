from utils.pdf_reader import DocumentChunk, split_text
from utils.retriever import retrieve_relevant_chunks


def test_overlap_preserves_boundary_information():
    text = "A" * 1100 + " annual leave entitlement is twenty days " + "B" * 1100
    chunks = split_text(text, chunk_size=1200, overlap=250)
    assert len(chunks) >= 2
    assert any("annual leave entitlement" in chunk for chunk in chunks)


def test_relevant_short_chunk_beats_long_irrelevant_chunk():
    chunks = (
        DocumentChunk("irrelevant.pdf", 1, 0, "company information " * 300),
        DocumentChunk("leave.pdf", 2, 0, "Employees receive twenty days of annual leave."),
    )
    matches = retrieve_relevant_chunks(chunks, "How many annual leave days do employees receive?", max_chunks=2)
    assert matches[0].chunk.source == "leave.pdf"


def test_punctuation_does_not_break_matching():
    chunks = (DocumentChunk("policy.pdf", 3, 0, "Maternity leave is available for eligible employees."),)
    matches = retrieve_relevant_chunks(chunks, "Maternity leave?", max_chunks=1)
    assert matches
    assert matches[0].chunk.source == "policy.pdf"
