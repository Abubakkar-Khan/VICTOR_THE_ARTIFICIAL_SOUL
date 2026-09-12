"""Robust Web Search Tool for Victor using DuckDuckGo."""

import asyncio
import urllib.parse
from typing import Any, Dict, List
import httpx
from bs4 import BeautifulSoup
from dexter.tools.base import BaseTool, PermissionLevel


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

    def intent_patterns(self) -> list[dict]:
        def extract_query(m) -> dict:
            query = m.group(1).strip().rstrip("?.!")
            if not query:
                return None
            lower = query.lower()
            if (lower.startswith("file") or 
                "file named" in lower or 
                "files named" in lower or 
                "my computer" in lower or 
                "this computer" in lower or 
                "my pc" in lower or 
                "on my pc" in lower or 
                "in downloads" in lower or 
                "in desktop" in lower or 
                "downloaded" in lower or 
                "youtube" in lower):
                return None
            return {"query": query}

        return [
            {"pattern": r"^(?:search(?:\s+the\s+web)?(?:\s+for)?|look\s+up|google|find(?:\s+information)?\s+about)\s+(.+)$", "extract": extract_query},
            {"pattern": r"^(?:what\s+is\s+the\s+latest|who\s+won|recent\s+news\s+on)\s+(.+)$", "extract": extract_query}
        ]

    def format_display(self, result) -> str:
        if not result.success:
            return f"I encountered an error executing {self.name}: {result.output}"
        out = result.output
        if isinstance(out, dict):
            query = out.get("query", "")
            hits = out.get("results", [])
            if not hits:
                return f"I searched the web for \"{query}\" but found no matching results."
            lines = [f"I searched for \"{query}\" and retrieved {len(hits)} relevant sources:"]
            for idx, item in enumerate(hits, 1):
                title = item.get("title", "")
                url = item.get("url", "")
                snippet = item.get("snippet", "")
                lines.append(f"{idx}. [{title}]({url})\n   {snippet}")
            return "\n\n".join(lines)
        return str(out)

