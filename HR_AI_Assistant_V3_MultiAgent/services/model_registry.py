from __future__ import annotations

from dataclasses import dataclass

from langchain_anthropic import ChatAnthropic
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

from config import settings
from services.langchain_crewai_llm import LangChainCrewLLM


@dataclass(frozen=True, slots=True)
class ProviderRuntime:
    provider: str
    model: str
    llm: LangChainCrewLLM


def configured_model_runtimes() -> list[ProviderRuntime]:
    runtimes: list[ProviderRuntime] = []

    if settings.openai_api_key:
        chat_model = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            timeout=settings.model_timeout_seconds,
            max_retries=2,
            use_responses_api=True,
        )
        runtimes.append(
            ProviderRuntime(
                provider="openai",
                model=settings.openai_model,
                llm=LangChainCrewLLM(
                    model=settings.openai_model,
                    chat_model=chat_model,
                    context_window=128_000,
                ),
            )
        )

    if settings.anthropic_api_key:
        chat_model = ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            timeout=settings.model_timeout_seconds,
            max_retries=2,
            max_tokens=settings.max_output_tokens,
        )
        runtimes.append(
            ProviderRuntime(
                provider="anthropic",
                model=settings.anthropic_model,
                llm=LangChainCrewLLM(
                    model=settings.anthropic_model,
                    chat_model=chat_model,
                    context_window=1_000_000,
                ),
            )
        )

    if settings.deepseek_api_key:
        chat_model = ChatDeepSeek(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            timeout=settings.model_timeout_seconds,
            max_retries=2,
            max_tokens=settings.max_output_tokens,
        )
        runtimes.append(
            ProviderRuntime(
                provider="deepseek",
                model=settings.deepseek_model,
                llm=LangChainCrewLLM(
                    model=settings.deepseek_model,
                    chat_model=chat_model,
                    context_window=128_000,
                ),
            )
        )

    return runtimes


def select_judge_runtime(runtimes: list[ProviderRuntime]) -> ProviderRuntime:
    preferred = next(
        (runtime for runtime in runtimes if runtime.provider == settings.judge_provider),
        None,
    )
    return preferred or runtimes[0]
