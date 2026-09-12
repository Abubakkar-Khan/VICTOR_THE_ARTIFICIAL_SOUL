"""Web Browser / Page Content Extraction Tool for Victor."""

import re
from typing import Any, Dict
import httpx
from dexter.tools.base import BaseTool, PermissionLevel

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class WebFetchTool(BaseTool):
    name = "web_fetch"
    description = "Fetch a webpage by URL and extract clean, readable text content (OpenClaw web_fetch standard)."
    permission = PermissionLevel.SAFE
    slash_command = "/fetch"
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Full HTTP or HTTPS URL to browse."
            },
            "max_characters": {
                "type": "integer",
                "description": "Maximum characters of text content to extract (default: 4000)."
            }
        },
        "required": ["url"]
    }

    async def run(self, url: str = "", max_characters: int = 4000, **kwargs: Any) -> Dict[str, Any]:
        target_url = url.strip()
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            target_url = "https://" + target_url

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 VictorAgent/0.1"
            )
        }

        async with httpx.AsyncClient(follow_redirects=True, timeout=12.0, headers=headers) as client:
            resp = await client.get(target_url)
            resp.raise_for_status()
            html = resp.text

        if BeautifulSoup:
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove scripts, styles, forms, navigation, footers
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
                tag.extract()

            title = soup.title.string.strip() if soup.title and soup.title.string else target_url
            
            # Extract readable text
            text = soup.get_text(separator="\n", strip=True)
            # Collapse excessive empty lines
            text = re.sub(r"\n{3,}", "\n\n", text)
        else:
            # Fallback simple regex stripper
            title = target_url
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()

        truncated = len(text) > max_characters
        content = text[:max_characters]

        return {
            "url": target_url,
            "title": title,
            "characters": len(content),
            "truncated": truncated,
            "content": content
        }

    def intent_patterns(self) -> list[dict]:
        def extract_url(m) -> dict:
            url = m.group(0)
            return {"url": url}

        def extract_cmd(m) -> dict:
            target = m.group(1).strip()
            if not target.startswith("http"):
                target = f"https://{target}"
            return {"url": target}

        return [
            {"pattern": r"^(?:fetch|read\s+url|read\s+webpage|scrape|get\s+page)\s+(.+)$", "extract": extract_cmd},
            {"pattern": r"^(?:browse|visit|open url)\s+(.+)$", "extract": extract_cmd},
            {"pattern": r"https?://[^\s]+", "extract": extract_url}
        ]

    def format_display(self, result) -> str:
        if not result.success:
            return f"I encountered an error executing {self.name}: {result.output}"
        out = result.output
        if isinstance(out, dict):
            title = out.get("title", "")
            url = out.get("url", "")
            content = out.get("content", "")
            return f"Content from [{title}]({url}):\n\n{content[:1200]}..."
        return str(out)


class BrowserTool(WebFetchTool):
    """Backwards-compatible alias for BrowserTool referencing WebFetchTool."""
    name = "browser"
    slash_command = "/browse"


