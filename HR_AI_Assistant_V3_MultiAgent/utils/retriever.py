from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Sequence

from utils.pdf_reader import DocumentChunk

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "how", "i", "if", "in", "is", "it", "may", "of", "on",
    "or", "our", "the", "their", "this", "to", "what", "when", "where",
    "which", "who", "why", "with", "you", "your",
}


@dataclass(frozen=True, slots=True)
class RetrievalMatch:
    chunk: DocumentChunk
    score: float


def tokenise(text: str) -> list[str]:
    tokens = re.findall(r"\b\w+\b", text.casefold(), flags=re.UNICODE)
    return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]


def _normalised_text(text: str) -> str:
    return " ".join(re.findall(r"\b\w+\b", text.casefold(), flags=re.UNICODE))


def _bm25_scores(chunks: Sequence[DocumentChunk], query_tokens: list[str]) -> list[float]:
    if not chunks or not query_tokens:
        return [0.0] * len(chunks)

    tokenised_docs = [tokenise(chunk.text) for chunk in chunks]
    document_frequencies: Counter[str] = Counter()
    for tokens in tokenised_docs:
        document_frequencies.update(set(tokens))

    document_count = len(tokenised_docs)
    avg_length = sum(len(tokens) for tokens in tokenised_docs) / max(document_count, 1)
    k1 = 1.5
    b = 0.75
    scores: list[float] = []

    for tokens in tokenised_docs:
        frequencies = Counter(tokens)
        length = len(tokens)
        score = 0.0
        for query_token in query_tokens:
            frequency = frequencies.get(query_token, 0)
            if not frequency:
                continue
            doc_frequency = document_frequencies[query_token]
            inverse_document_frequency = math.log(
                1 + (document_count - doc_frequency + 0.5) / (doc_frequency + 0.5)
            )
            denominator = frequency + k1 * (1 - b + b * length / max(avg_length, 1))
            score += inverse_document_frequency * (frequency * (k1 + 1)) / denominator
        scores.append(score)
    return scores


def _lexical_bonus(chunk: DocumentChunk, question: str, query_tokens: list[str]) -> float:
    chunk_normalised = _normalised_text(chunk.text)
    question_normalised = _normalised_text(question)
    chunk_tokens = set(tokenise(chunk.text))
    query_token_set = set(query_tokens)

    coverage = len(chunk_tokens & query_token_set) / max(len(query_token_set), 1)
    bonus = coverage * 2.5

    if question_normalised and question_normalised in chunk_normalised:
        bonus += 5.0

    # Reward adjacent query terms, useful for policy names and multi-word entitlements.
    for left, right in zip(query_tokens, query_tokens[1:]):
        if f"{left} {right}" in chunk_normalised:
            bonus += 0.5

    return bonus


def retrieve_relevant_chunks(
    chunks: Sequence[DocumentChunk],
    question: str,
    max_chunks: int = 8,
    minimum_score: float = 0.05,
) -> list[RetrievalMatch]:
    query_tokens = tokenise(question)
    if not chunks or not query_tokens:
        return []

    bm25 = _bm25_scores(chunks, query_tokens)
    ranked = [
        RetrievalMatch(
            chunk=chunk,
            score=bm25_score + _lexical_bonus(chunk, question, query_tokens),
        )
        for chunk, bm25_score in zip(chunks, bm25)
    ]
    ranked.sort(key=lambda item: item.score, reverse=True)
    primary = [item for item in ranked if item.score >= minimum_score][:max_chunks]

    # Include immediately adjacent chunks so an answer split at a boundary remains available.
    by_location = {
        (chunk.source, chunk.page, chunk.chunk_index): chunk for chunk in chunks
    }
    selected: dict[tuple[str, int, int], RetrievalMatch] = {}
    for item in primary:
        key = (item.chunk.source, item.chunk.page, item.chunk.chunk_index)
        selected[key] = item
        for neighbour_index in (item.chunk.chunk_index - 1, item.chunk.chunk_index + 1):
            neighbour_key = (item.chunk.source, item.chunk.page, neighbour_index)
            neighbour = by_location.get(neighbour_key)
            if neighbour and neighbour_key not in selected:
                selected[neighbour_key] = RetrievalMatch(
                    chunk=neighbour,
                    score=max(item.score - 0.25, 0.0),
                )

    result = sorted(selected.values(), key=lambda item: item.score, reverse=True)
    return result[: max_chunks + 2]


def build_context(matches: Iterable[RetrievalMatch]) -> str:
    sections: list[str] = []
    for item in matches:
        sections.append(
            f"[Source: {item.chunk.source}, page {item.chunk.page}]\n{item.chunk.text}"
        )
    return "\n\n---\n\n".join(sections)
