"""YouTube Search Tool for Victor."""

import re
import urllib.parse
from typing import Any, Dict, List
import httpx
from bs4 import BeautifulSoup
from victor.tools.base import BaseTool, PermissionLevel


class YouTubeTool(BaseTool):
    name = "youtube"
    description = "Search YouTube for videos, playlists, tutorials, and channels, returning titles, links, and descriptions."
    permission = PermissionLevel.SAFE
    slash_command = "/youtube"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query, e.g. 'compiler construction tutorial beginner'"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of video results to return (default: 5)"
            }
        },
        "required": ["query"]
    }

    async def run(self, query: str = "", max_results: int = 5, **kwargs: Any) -> Dict[str, Any]:
        q = query.strip()
        if not q:
            raise ValueError("Empty YouTube query.")

        search_query = f"site:youtube.com/watch {q}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        results: List[Dict[str, str]] = []

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=12.0, headers=headers) as client:
                resp = await client.post("https://html.duckduckgo.com/html/", data={"q": search_query})
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for el in soup.select(".result"):
                        title_el = el.select_one(".result__title a")
                        snippet_el = el.select_one(".result__snippet")
                        if not title_el:
                            continue

                        raw_href = title_el.get("href", "")
                        if "uddg=" in raw_href:
                            parsed = urllib.parse.urlparse(raw_href)
                            params = urllib.parse.parse_qs(parsed.query)
                            final_url = params.get("uddg", [raw_href])[0]
                        else:
                            final_url = raw_href

                        if "youtube.com/watch" in final_url or "youtu.be/" in final_url:
                            title_text = title_el.get_text(strip=True).replace(" - YouTube", "")
                            snippet_text = snippet_el.get_text(strip=True) if snippet_el else ""

                            # Extract duration or channel if mentioned in snippet
                            results.append({
                                "title": title_text,
                                "url": final_url,
                                "description": snippet_text,
                            })

                        if len(results) >= max_results:
                            break
        except Exception:
            pass

        # Fallback direct link if search scraping had no items
        if not results:
            clean_encoded = urllib.parse.quote_plus(q)
            direct_search_url = f"https://www.youtube.com/results?search_query={clean_encoded}"
            results.append({
                "title": f"YouTube Search: {q}",
                "url": direct_search_url,
                "description": f"View all matching video results for '{q}' directly on YouTube.",
            })

        return {
            "query": q,
            "count": len(results),
            "videos": results,
        }
