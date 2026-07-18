from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from config import MCP_SERVER_PATH, settings
from utils.pdf_reader import get_knowledge_base_version, read_all_pdfs
from utils.retriever import build_context, retrieve_relevant_chunks


class MCPRetrievalError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RetrievedPolicyContext:
    context: str
    matches: list[dict[str, Any]]
    knowledge_base_version: str
    retrieval_mode: str


def _extract_text(result: Any) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        if isinstance(result.get("text"), str):
            return result["text"]
        if isinstance(result.get("content"), str):
            return result["content"]
        return json.dumps(result, ensure_ascii=False)
    if isinstance(result, list):
        parts: list[str] = []
        for item in result:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text)
            else:
                text = getattr(item, "text", None)
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    text = getattr(result, "text", None)
    return text if isinstance(text, str) else str(result)


async def _retrieve_through_mcp(question: str, max_chunks: int) -> RetrievedPolicyContext:
    if settings.mcp_server_url:
        server_config: dict[str, Any] = {
            "transport": "http",
            "url": settings.mcp_server_url,
        }
    else:
        server_config = {
            "transport": "stdio",
            "command": sys.executable,
            "args": [str(MCP_SERVER_PATH)],
            "env": {
                **os.environ,
                "PYTHONPATH": str(MCP_SERVER_PATH.parent),
            },
        }

    client = MultiServerMCPClient({"hr_policy": server_config})
    tools = await client.get_tools()
    search_tool = next(
        (tool for tool in tools if tool.name == "search_hr_policies"),
        None,
    )
    if search_tool is None:
        raise MCPRetrievalError("The MCP search_hr_policies tool is unavailable.")

    raw_result = await search_tool.ainvoke(
        {"question": question, "max_chunks": max_chunks}
    )
    raw_text = _extract_text(raw_result).strip()
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise MCPRetrievalError("The MCP server returned invalid JSON.") from exc

    if payload.get("error"):
        raise MCPRetrievalError(str(payload["error"]))
    context = str(payload.get("context", "")).strip()
    matches = payload.get("matches") or []
    if not context or not matches:
        raise MCPRetrievalError(
            "No sufficiently relevant policy passage was found through MCP."
        )
    return RetrievedPolicyContext(
        context=context,
        matches=list(matches),
        knowledge_base_version=str(payload.get("knowledge_base_version", "")),
        retrieval_mode="mcp",
    )


def _retrieve_directly(question: str, max_chunks: int) -> RetrievedPolicyContext:
    from config import DATA_FOLDER

    chunks = read_all_pdfs(str(DATA_FOLDER))
    matches = retrieve_relevant_chunks(chunks, question, max_chunks=max_chunks)
    if not matches:
        raise MCPRetrievalError("No sufficiently relevant policy passage was found.")
    return RetrievedPolicyContext(
        context=build_context(matches),
        matches=[
            {
                "document": item.chunk.source,
                "page": item.chunk.page,
                "chunk_index": item.chunk.chunk_index,
                "score": round(item.score, 6),
                "text": item.chunk.text,
            }
            for item in matches
        ],
        knowledge_base_version=get_knowledge_base_version(DATA_FOLDER),
        retrieval_mode="direct-fallback",
    )


async def retrieve_policy_context(
    question: str,
    max_chunks: int,
) -> RetrievedPolicyContext:
    try:
        return await _retrieve_through_mcp(question, max_chunks)
    except Exception as exc:
        if not settings.direct_retrieval_fallback:
            if isinstance(exc, MCPRetrievalError):
                raise
            raise MCPRetrievalError("MCP retrieval failed.") from exc
        return _retrieve_directly(question, max_chunks)
