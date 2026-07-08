"""A lightweight Serper-based tool for finding publicly indexed Facebook content."""

from __future__ import annotations

import os
from typing import Any

import requests
from crewai.tools import tool


@tool("Search public Facebook content")
def search_public_facebook(query: str) -> str:
    """Search publicly indexed Facebook pages and posts related to a query.

    This tool uses Google results through Serper and restricts the query to
    facebook.com. It cannot access private profiles, private groups, content
    requiring login, or content that search engines have not indexed.
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return (
            "Facebook search was skipped because SERPER_API_KEY is not configured. "
            "Use the supplied product information and clearly label unsupported "
            "claims as assumptions."
        )

    search_query = query.strip()
    if not search_query:
        return "Facebook search received an empty query."

    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            json={
                "q": f"site:facebook.com {search_query}",
                "num": 8,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    except requests.RequestException as exc:
        return f"Facebook search failed: {exc}"
    except ValueError:
        return "Facebook search failed because the provider returned invalid JSON."

    organic = payload.get("organic", [])
    if not organic:
        return (
            "No publicly indexed Facebook results were found. This does not prove "
            "that no relevant Facebook content exists."
        )

    formatted_results: list[str] = []
    for index, result in enumerate(organic[:8], start=1):
        title = result.get("title", "Untitled result")
        link = result.get("link", "No link")
        snippet = result.get("snippet", "No snippet available")
        formatted_results.append(
            f"{index}. Title: {title}\n"
            f"   Link: {link}\n"
            f"   Snippet: {snippet}"
        )

    return (
        "Publicly indexed Facebook search results:\n\n"
        + "\n\n".join(formatted_results)
        + "\n\nTreat snippets as leads, not as fully verified source content."
    )
