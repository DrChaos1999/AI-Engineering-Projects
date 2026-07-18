from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
DATA_FOLDER = BASE_DIR / "data"
STATIC_FOLDER = BASE_DIR / "static"
ASSETS_FOLDER = BASE_DIR / "assets"
DATABASE_PATH = BASE_DIR / "database" / "hr_ai.db"
MCP_SERVER_PATH = BASE_DIR / "mcp_server.py"

load_dotenv(ENV_PATH, encoding="utf-8-sig")


def _as_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().casefold() in {"1", "true", "yes", "on"}


def _as_int(name: str, default: int, minimum: int, maximum: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc
    return max(minimum, min(value, maximum))


@dataclass(frozen=True, slots=True)
class CustomerPlan:
    code: str
    minutes: int
    max_questions: int


def parse_customer_plans(raw: str) -> dict[str, CustomerPlan]:
    """Parse code:minutes:max_questions entries separated by commas."""
    plans: dict[str, CustomerPlan] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        parts = [part.strip() for part in entry.split(":")]
        if len(parts) != 3 or not parts[0]:
            raise RuntimeError(
                "CUSTOMER_PLANS must use code:minutes:max_questions entries."
            )
        code, minutes_text, questions_text = parts
        try:
            minutes = int(minutes_text)
            max_questions = int(questions_text)
        except ValueError as exc:
            raise RuntimeError(
                "CUSTOMER_PLANS minutes and max_questions must be integers."
            ) from exc
        if minutes < 1 or minutes > 1440:
            raise RuntimeError("Customer plan minutes must be between 1 and 1440.")
        if max_questions < 0 or max_questions > 10000:
            raise RuntimeError("Customer plan max_questions must be between 0 and 10000.")
        plans[code] = CustomerPlan(code, minutes, max_questions)
    return plans


@dataclass(frozen=True, slots=True)
class Settings:
    openai_api_key: str
    anthropic_api_key: str
    deepseek_api_key: str
    openai_model: str
    anthropic_model: str
    deepseek_model: str
    judge_provider: str
    model_timeout_seconds: int
    max_output_tokens: int
    retrieval_chunks: int
    max_upload_mb: int
    default_session_minutes: int
    default_max_questions: int
    require_access_code: bool
    customer_plans: dict[str, CustomerPlan]
    session_cookie_name: str
    cookie_secure: bool
    admin_upload_token: str
    access_code_pepper: str
    mcp_server_url: str
    direct_retrieval_fallback: bool
    parallel_candidates: bool

    @property
    def configured_providers(self) -> list[str]:
        providers: list[str] = []
        if self.openai_api_key:
            providers.append("openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.deepseek_api_key:
            providers.append("deepseek")
        return providers


settings = Settings(
    openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "").strip(),
    deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
    openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip(),
    anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5").strip(),
    deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip(),
    judge_provider=os.getenv("JUDGE_PROVIDER", "openai").strip().casefold(),
    model_timeout_seconds=_as_int("MODEL_TIMEOUT_SECONDS", 90, 10, 300),
    max_output_tokens=_as_int("MAX_OUTPUT_TOKENS", 900, 200, 8000),
    retrieval_chunks=_as_int("RETRIEVAL_CHUNKS", 8, 2, 20),
    max_upload_mb=_as_int("MAX_UPLOAD_MB", 20, 1, 200),
    default_session_minutes=_as_int("DEFAULT_SESSION_MINUTES", 10, 1, 1440),
    default_max_questions=_as_int("DEFAULT_MAX_QUESTIONS", 10, 0, 10000),
    require_access_code=_as_bool("REQUIRE_ACCESS_CODE", False),
    customer_plans=parse_customer_plans(os.getenv("CUSTOMER_PLANS", "")),
    session_cookie_name=os.getenv("SESSION_COOKIE_NAME", "hr_session").strip(),
    cookie_secure=_as_bool("COOKIE_SECURE", False),
    admin_upload_token=os.getenv("ADMIN_UPLOAD_TOKEN", "").strip(),
    access_code_pepper=os.getenv("ACCESS_CODE_PEPPER", "").strip(),
    mcp_server_url=os.getenv("MCP_SERVER_URL", "").strip(),
    direct_retrieval_fallback=_as_bool("DIRECT_RETRIEVAL_FALLBACK", True),
    parallel_candidates=_as_bool("PARALLEL_CANDIDATES", True),
)

DATA_FOLDER.mkdir(parents=True, exist_ok=True)
