import re
from typing import Any, Dict, Optional, Tuple

from victor.tools.registry import ToolRegistry


class ToolRouter:
    """Routes user input to the correct tool based on intent patterns."""
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def route(self, user_input: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Iterates all registered tools, checks their intent_patterns, and returns (tool_name, extracted_params)."""
        cleaned = user_input.strip()
        lower = cleaned.lower()

        for tool in self.registry.list_tools():
            patterns = tool.intent_patterns()
            for pattern_dict in patterns:
                pattern = pattern_dict.get("pattern", "")
                m = re.match(pattern, lower) or re.search(pattern, cleaned)
                if m:
                    extract = pattern_dict.get("extract")
                    params = {}
                    
                    if callable(extract):
                        # Allow custom extraction logic
                        params = extract(m)
                    elif isinstance(extract, str):
                        # Single parameter extracted from group 1 or group 0
                        val = m.group(1).strip() if m.lastindex else m.group(0).strip()
                        params[extract] = val
                    elif isinstance(extract, dict):
                        # Dictionary for static params or mapping
                        for k, v in extract.items():
                            if isinstance(v, int):
                                params[k] = m.group(v)
                            else:
                                params[k] = v

                    if params:
                        return (tool.name, params)

        return None

