from __future__ import annotations

import json
from typing import Any

from crewai import BaseLLM
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import Field


class LangChainCrewLLM(BaseLLM):
    """Expose any LangChain chat model through CrewAI's BaseLLM contract."""

    llm_type: str = "langchain-chat-model"
    provider: str = "langchain"
    chat_model: BaseChatModel = Field(exclude=True)
    context_window: int = 128_000

    def call(
        self,
        messages: str | list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        from_task: Any = None,
        from_agent: Any = None,
        response_model: Any = None,
    ) -> str:
        del tools, available_functions, from_task, from_agent, response_model
        langchain_messages = self._convert_messages(messages)
        # CrewAI callbacks are not LangChain callback handlers.
        # Do not forward TokenCalcHandler into LangChain.
        del callbacks

        response = self.chat_model.invoke(langchain_messages)
        answer = self._content_to_text(response.content).strip()
        if not answer:
            raise RuntimeError(f"{self.model} returned an empty response.")
        return answer

    @staticmethod
    def _convert_messages(
        messages: str | list[dict[str, Any]],
    ) -> list[BaseMessage]:
        if isinstance(messages, str):
            return [HumanMessage(content=messages)]

        converted: list[BaseMessage] = []
        for message in messages:
            role = str(message.get("role", "user")).casefold()
            content = message.get("content", "")
            if not isinstance(content, (str, list)):
                content = json.dumps(content, ensure_ascii=False)
            if role == "system":
                converted.append(SystemMessage(content=content))
            elif role in {"assistant", "ai"}:
                converted.append(AIMessage(content=content))
            elif role == "tool":
                converted.append(
                    ToolMessage(
                        content=content,
                        tool_call_id=str(message.get("tool_call_id", "tool")),
                    )
                )
            else:
                converted.append(HumanMessage(content=content))
        return converted

    @staticmethod
    def _content_to_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict):
                    text = block.get("text") or block.get("content")
                    if isinstance(text, str):
                        parts.append(text)
                else:
                    text = getattr(block, "text", None)
                    if isinstance(text, str):
                        parts.append(text)
            return "\n".join(parts)
        return str(content)

    def supports_function_calling(self) -> bool:
        # Retrieval is performed before the crew runs, through LangChain's MCP
        # client. These answer/judge agents intentionally do not call tools.
        return False

    def supports_stop_words(self) -> bool:
        return False

    def get_context_window_size(self) -> int:
        return self.context_window
