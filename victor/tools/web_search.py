"""Robust Web Search Tool for Victor using DuckDuckGo."""

import asyncio
import urllib.parse
from typing import Any, Dict, List
import httpx
from bs4 import BeautifulSoup
from victor.tools.base import BaseTool, PermissionLevel


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the internet and return structured search results with titles, snippets, and URLs."
    permission = PermissionLevel.SAFE
    slash_command = "/search"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query, e.g. 'compiler optimization advances'"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of search results to return (default: 5)"
            }
        },
        "required": ["query"]
    }

    async def run(self, query: str = "", max_results: int = 5, **kwargs: Any) -> Dict[str, Any]:
        q = query.strip()
        if not q:
            raise ValueError("Empty search query.")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        async with httpx.AsyncClient(follow_redirects=True, timeout=12.0, headers=headers) as client:
            resp = await client.post("https://html.duckduckgo.com/html/", data={"q": q})
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")
        results: List[Dict[str, str]] = []

        for el in soup.select(".result"):
            title_el = el.select_one(".result__title a")
            snippet_el = el.select_one(".result__snippet")
            if not title_el or not snippet_el:
                continue

            raw_href = title_el.get("href", "")
            # DuckDuckGo wraps URLs in /l/?uddg=<encoded_url>
            if "uddg=" in raw_href:
                parsed = urllib.parse.urlparse(raw_href)
                params = urllib.parse.parse_qs(parsed.query)
                final_url = params.get("uddg", [raw_href])[0]
            else:
                final_url = raw_href

            title_text = title_el.get_text(strip=True)
            snippet_text = snippet_el.get_text(strip=True)

            results.append({
                "title": title_text,
                "url": final_url,
                "snippet": snippet_text,
            })

            if len(results) >= max_results:
                break

        return {
            "query": q,
            "count": len(results),
            "results": results
        }
