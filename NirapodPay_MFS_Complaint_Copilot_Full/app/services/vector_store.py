import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.schemas import KnowledgeHit


class PseudoVectorStore:
    """Small local vector index based on TF-IDF and cosine similarity."""

    def __init__(self, articles: list[dict]) -> None:
        if not articles:
            raise ValueError("Knowledge base must contain at least one article.")
        self.articles = articles
        self.documents = [self._article_to_text(article) for article in articles]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2), stop_words="english", lowercase=True, sublinear_tf=True
        )
        self.matrix = self.vectorizer.fit_transform(self.documents)

    @staticmethod
    def _article_to_text(article: dict) -> str:
        return " ".join([
            article.get("title", ""),
            article.get("category", ""),
            " ".join(article.get("symptoms", [])),
            article.get("resolution", ""),
            " ".join(article.get("routing_keywords", [])),
        ])

    @classmethod
    def from_json(cls, path: str | Path) -> "PseudoVectorStore":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def search(self, query: str, top_k: int = 3, category: str | None = None) -> list[KnowledgeHit]:
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix)[0]
        hits: list[KnowledgeHit] = []

        for raw_index in scores.argsort()[::-1]:
            index = int(raw_index)
            article = self.articles[index]
            if category and article.get("category") not in {category, "general"}:
                continue
            score = float(scores[index])
            if score <= 0 and hits:
                continue
            hits.append(KnowledgeHit(
                article_id=article["article_id"],
                title=article["title"],
                category=article["category"],
                score=round(score, 4),
                resolution=article["resolution"],
            ))
            if len(hits) >= top_k:
                break
        return hits
