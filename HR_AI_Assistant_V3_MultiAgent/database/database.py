from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_DB_PATH = Path(__file__).resolve().parent / "hr_ai.db"


class SessionError(RuntimeError):
    pass


class SessionExpired(SessionError):
    pass


class QuestionLimitReached(SessionError):
    pass


@dataclass(frozen=True, slots=True)
class CachedAnswer:
    answer: str
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SessionStatus:
    session_id: str
    started_at: int
    expires_at: int
    remaining_seconds: int
    question_count: int
    max_questions: int
    active: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "expires_at": self.expires_at,
            "remaining_seconds": self.remaining_seconds,
            "question_count": self.question_count,
            "max_questions": self.max_questions,
            "questions_remaining": (
                None
                if self.max_questions == 0
                else max(self.max_questions - self.question_count, 0)
            ),
            "active": self.active,
        }


def _normalise_question(question: str) -> str:
    return re.sub(r"\s+", " ", question.casefold()).strip()


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(_DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def create_database(path: Path | None = None) -> None:
    global _DB_PATH
    if path is not None:
        _DB_PATH = path.resolve()
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with _connect() as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS answer_cache (
                question_key TEXT NOT NULL,
                knowledge_base_version TEXT NOT NULL,
                answer TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (question_key, knowledge_base_version)
            )
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(answer_cache)").fetchall()
        }
        if "metadata_json" not in columns:
            connection.execute(
                "ALTER TABLE answer_cache ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'"
            )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS customer_sessions (
                session_id TEXT PRIMARY KEY,
                access_key_hash TEXT UNIQUE,
                started_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                last_seen_at INTEGER NOT NULL,
                question_count INTEGER NOT NULL DEFAULT 0,
                max_questions INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON customer_sessions(expires_at)"
        )


def get_cached_answer(
    question: str,
    knowledge_base_version: str,
) -> CachedAnswer | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT answer, metadata_json
            FROM answer_cache
            WHERE question_key = ? AND knowledge_base_version = ?
            """,
            (_normalise_question(question), knowledge_base_version),
        ).fetchone()
    if row is None:
        return None
    try:
        metadata = json.loads(row["metadata_json"] or "{}")
    except json.JSONDecodeError:
        metadata = {}
    return CachedAnswer(answer=row["answer"], metadata=metadata)


def save_answer(
    question: str,
    knowledge_base_version: str,
    answer: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO answer_cache (
                question_key,
                knowledge_base_version,
                answer,
                metadata_json
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(question_key, knowledge_base_version)
            DO UPDATE SET
                answer = excluded.answer,
                metadata_json = excluded.metadata_json,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                _normalise_question(question),
                knowledge_base_version,
                answer,
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )


def clear_answer_cache() -> None:
    with _connect() as connection:
        connection.execute("DELETE FROM answer_cache")


def _row_to_session(row: sqlite3.Row, now: int | None = None) -> SessionStatus:
    current = int(time.time()) if now is None else now
    remaining = max(int(row["expires_at"]) - current, 0)
    question_count = int(row["question_count"])
    max_questions = int(row["max_questions"])
    active = remaining > 0 and (
        max_questions == 0 or question_count < max_questions
    )
    return SessionStatus(
        session_id=row["session_id"],
        started_at=int(row["started_at"]),
        expires_at=int(row["expires_at"]),
        remaining_seconds=remaining,
        question_count=question_count,
        max_questions=max_questions,
        active=active,
    )


def get_session_status(session_id: str) -> SessionStatus | None:
    if not session_id:
        return None
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM customer_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    return _row_to_session(row) if row else None


def get_or_create_session(
    *,
    existing_session_id: str | None,
    access_key_hash: str | None,
    limit_minutes: int,
    max_questions: int,
) -> SessionStatus:
    now = int(time.time())
    expires_at = now + limit_minutes * 60

    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")

        if existing_session_id:
            row = connection.execute(
                "SELECT * FROM customer_sessions WHERE session_id = ?",
                (existing_session_id,),
            ).fetchone()
            if row:
                connection.commit()
                return _row_to_session(row, now)

        if access_key_hash:
            row = connection.execute(
                "SELECT * FROM customer_sessions WHERE access_key_hash = ?",
                (access_key_hash,),
            ).fetchone()
            if row:
                connection.commit()
                return _row_to_session(row, now)

        session_id = str(uuid.uuid4())
        connection.execute(
            """
            INSERT INTO customer_sessions (
                session_id,
                access_key_hash,
                started_at,
                expires_at,
                last_seen_at,
                question_count,
                max_questions
            )
            VALUES (?, ?, ?, ?, ?, 0, ?)
            """,
            (
                session_id,
                access_key_hash,
                now,
                expires_at,
                now,
                max_questions,
            ),
        )
        row = connection.execute(
            "SELECT * FROM customer_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        connection.commit()
    if row is None:
        raise SessionError("The session could not be created.")
    return _row_to_session(row, now)


def consume_question(session_id: str) -> SessionStatus:
    now = int(time.time())
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM customer_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            connection.rollback()
            raise SessionError("Start a customer session before asking a question.")

        if int(row["expires_at"]) <= now:
            connection.rollback()
            raise SessionExpired("This customer session has expired.")

        max_questions = int(row["max_questions"])
        question_count = int(row["question_count"])
        if max_questions and question_count >= max_questions:
            connection.rollback()
            raise QuestionLimitReached(
                "This customer session has reached its question limit."
            )

        connection.execute(
            """
            UPDATE customer_sessions
            SET question_count = question_count + 1, last_seen_at = ?
            WHERE session_id = ?
            """,
            (now, session_id),
        )
        updated = connection.execute(
            "SELECT * FROM customer_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        connection.commit()
    if updated is None:
        raise SessionError("The session could not be updated.")
    return _row_to_session(updated, now)


def delete_session_by_access_hash(access_key_hash: str) -> None:
    """Administrative helper for resetting a one-time access-code allocation."""
    with _connect() as connection:
        connection.execute(
            "DELETE FROM customer_sessions WHERE access_key_hash = ?",
            (access_key_hash,),
        )
