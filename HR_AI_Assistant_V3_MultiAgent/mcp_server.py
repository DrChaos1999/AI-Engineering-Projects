from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP

from config import DATA_FOLDER
from utils.pdf_reader import get_knowledge_base_version, read_all_pdfs
from utils.retriever import build_context, retrieve_relevant_chunks

mcp = FastMCP(
    "HR Policy Knowledge Server",
    json_response=True,
    stateless_http=True,
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "8001")),
)


@mcp.tool()
def search_hr_policies(question: str, max_chunks: int = 8) -> str:
    """Retrieve the strongest grounded HR-policy passages for a question."""
    cleaned = " ".join(question.split())
    if not cleaned:
        return json.dumps({"error": "Question must not be empty."})

    chunks = read_all_pdfs(str(DATA_FOLDER))
    matches = retrieve_relevant_chunks(
        chunks,
        cleaned,
        max_chunks=max(2, min(max_chunks, 20)),
    )
    payload = {
        "question": cleaned,
        "knowledge_base_version": get_knowledge_base_version(DATA_FOLDER),
        "context": build_context(matches),
        "matches": [
            {
                "document": item.chunk.source,
                "page": item.chunk.page,
                "chunk_index": item.chunk.chunk_index,
                "score": round(item.score, 6),
                "text": item.chunk.text,
            }
            for item in matches
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


@mcp.tool()
def list_hr_documents() -> str:
    """List the PDF documents currently indexed by the HR assistant."""
    return json.dumps(
        {"documents": sorted(path.name for path in DATA_FOLDER.glob("*.pdf"))},
        ensure_ascii=False,
    )


@mcp.resource("hr://documents")
def document_catalogue() -> str:
    """Expose the current document catalogue as an MCP resource."""
    return list_hr_documents()


if __name__ == "__main__":
    # Stdio is ideal locally. Set MCP_TRANSPORT=streamable-http to deploy the
    # same tool server separately at http://MCP_HOST:MCP_PORT/mcp.
    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().casefold()
    if transport not in {"stdio", "streamable-http", "sse"}:
        raise RuntimeError("MCP_TRANSPORT must be stdio, streamable-http, or sse.")
    mcp.run(transport=transport)
