from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    source: str
    page: int
    chunk_index: int
    text: str


def _normalise_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text(text: str, chunk_size: int = 1200, overlap: int = 250) -> list[str]:
    """Create overlapping chunks and avoid cutting words when possible."""
    text = _normalise_text(text)
    if not text:
        return []
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        tentative_end = min(start + chunk_size, text_length)
        end = tentative_end

        if tentative_end < text_length:
            boundary_candidates = [
                text.rfind("\n\n", start + chunk_size // 2, tentative_end),
                text.rfind(". ", start + chunk_size // 2, tentative_end),
                text.rfind(" ", start + chunk_size // 2, tentative_end),
            ]
            best_boundary = max(boundary_candidates)
            if best_boundary > start:
                end = best_boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break
        start = max(end - overlap, start + 1)

    return chunks


def _extract_with_pdfplumber(pdf_path: Path) -> list[str]:
    pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(_normalise_text(page.extract_text(x_tolerance=2, y_tolerance=3) or ""))
    return pages


def _extract_with_pymupdf(pdf_path: Path) -> list[str]:
    document = fitz.open(pdf_path)
    try:
        return [_normalise_text(page.get_text("text") or "") for page in document]
    finally:
        document.close()


def _read_pdf_pages(pdf_path: Path) -> list[str]:
    try:
        pages = _extract_with_pdfplumber(pdf_path)
    except Exception:
        pages = []

    # Fallback when pdfplumber fails or extracts almost nothing.
    if sum(len(page) for page in pages) < 50:
        try:
            pages = _extract_with_pymupdf(pdf_path)
        except Exception:
            pages = []
    return pages


@lru_cache(maxsize=8)
def read_all_pdfs(folder_path: str) -> tuple[DocumentChunk, ...]:
    folder = Path(folder_path).resolve()
    chunks: list[DocumentChunk] = []

    for pdf_path in sorted(folder.glob("*.pdf")):
        pages = _read_pdf_pages(pdf_path)
        for page_number, page_text in enumerate(pages, start=1):
            for chunk_index, chunk_text in enumerate(split_text(page_text)):
                chunks.append(
                    DocumentChunk(
                        source=pdf_path.name,
                        page=page_number,
                        chunk_index=chunk_index,
                        text=chunk_text,
                    )
                )
    return tuple(chunks)


def get_knowledge_base_version(folder: Path) -> str:
    """Hash file names, sizes, and modification times for cache invalidation."""
    digest = hashlib.sha256()
    for path in sorted(folder.glob("*.pdf")):
        stat = path.stat()
        digest.update(path.name.encode("utf-8"))
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
    return digest.hexdigest()
