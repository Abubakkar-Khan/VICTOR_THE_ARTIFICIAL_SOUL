"""Ollama Model Provider implementation for Victor."""

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx
from dexter.models.base import BaseLLM, ChatMessage, LLMResponse


class OllamaProvider(BaseLLM):
    """Integrates Victor with local Ollama models (e.g. Qwen 1.5B, 2B, 3B)."""

    def __init__(
        self,
        model_name: str = "qwen2:1.5b",
        api_base: str = "http://127.0.0.1:11434",
        fallback_model: Optional[str] = "qwen3.5:2b",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        super().__init__(
            model_name=model_name,
            api_base=api_base.rstrip("/"),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.fallback_model = fallback_model
        self._verified_model: Optional[str] = None

    async def list_available_models(self) -> List[str]:
        """Fetch list of available model tag names from Ollama."""
        detailed = await self.list_available_models_detailed()
        return [m["name"] for m in detailed if m.get("name")]

    async def list_available_models_detailed(self) -> List[Dict[str, Any]]:
        """Fetch list of available models with rich metadata from Ollama (with CLI fallback)."""
        # 1. Try HTTP API with 3.5s timeout
        try:
            async with httpx.AsyncClient(trust_env=False, timeout=3.5) as client:
                res = await client.get(f"{self.api_base}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models_raw = data.get("models", [])
                    results = []
                    for m in models_raw:
                        name = m.get("name") or m.get("model") or ""
                        if not name:
                            continue
                        size_bytes = m.get("size", 0)
                        details = m.get("details", {})
                        param_size = details.get("parameter_size", "")
                        family = details.get("family", "")

                        if size_bytes >= 1024 * 1024 * 1024:
                            size_str = f"{size_bytes / (1024**3):.1f} GB"
                        elif size_bytes >= 1024 * 1024:
                            size_str = f"{size_bytes / (1024**2):.0f} MB"
                        else:
                            size_str = f"{size_bytes} B"

                        label = f"{name} ({param_size} · {size_str})" if param_size else f"{name} ({size_str})"
                        is_small = any(k in name.lower() for k in ["0.5b", "1b", "1.5b", "2b", "3b", "620m", "360m", "135m"])

                        results.append({
                            "name": name,
                            "label": label,
                            "size": size_bytes,
                            "size_str": size_str,
                            "parameter_size": param_size,
                            "family": family,
                            "is_small": is_small,
                            "modified_at": m.get("modified_at", ""),
                        })
                    if results:
                        return results
        except Exception:
            pass

        # 2. CLI fallback: 'ollama list'
        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama", "list",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3.0)
            lines = stdout.decode("utf-8", errors="ignore").splitlines()
            results = []
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    name = parts[0]
                    size_str = f"{parts[2]} {parts[3]}" if len(parts) >= 4 else ""
                    is_small = any(k in name.lower() for k in ["0.5b", "1b", "1.5b", "2b", "3b", "620m"])
                    results.append({
                        "name": name,
                        "label": f"{name} ({size_str})" if size_str else name,
                        "size": 0,
                        "size_str": size_str,
                        "parameter_size": "",
                        "family": "",
                        "is_small": is_small,
                        "modified_at": "",
                    })
            if results:
                return results
        except Exception:
            pass

        return []

    async def resolve_active_model(self) -> str:
        """Resolve the model to use, falling back if the configured model is missing."""
        if self._verified_model:
            return self._verified_model

        models = await self.list_available_models()
        if not models:
            self._verified_model = self.model_name
            return self.model_name

        # Exact match or prefix match
        for candidate in [self.model_name, self.fallback_model]:
            if candidate and candidate in models:
                self._verified_model = candidate
                return candidate
            if candidate:
                for m in models:
                    if m.startswith(candidate) or candidate in m:
                        self._verified_model = m
                        return m

        # Fallback to any qwen model, or first available
        for m in models:
            if "qwen" in m.lower():
                self._verified_model = m
                return m

        self._verified_model = models[0] if models else self.model_name
        return self._verified_model

    async def is_available(self) -> bool:
        """Check if Ollama is running and responding."""
        try:
            async with httpx.AsyncClient(trust_env=False, timeout=1.5) as client:
                res = await client.get(f"{self.api_base}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def _prepare_payload(
        self,
        active_model: str,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})

        options: Dict[str, Any] = {
            "temperature": temperature if temperature is not None else self.temperature,
        }
        if max_tokens:
            options["num_predict"] = max_tokens
        elif self.max_tokens:
            options["num_predict"] = self.max_tokens

        return {
            "model": active_model,
            "messages": formatted_messages,
            "stream": stream,
            "options": options,
        }

    async def generate(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        active_model = await self.resolve_active_model()
        payload = self._prepare_payload(
            active_model,
            messages,
            system_prompt,
            temperature,
            max_tokens,
            stream=False,
        )

        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(f"{self.api_base}/api/chat", json=payload)
                if res.status_code != 200:
                    try:
                        err_json = res.json()
                        err_msg = err_json.get("error", res.text)
                    except Exception:
                        err_msg = res.text
                    
                    hint = ""
                    if "memory" in err_msg.lower() or "terminated" in err_msg.lower():
                        hint = "\n\n*(Notice: System physical memory is currently low. Freeing up RAM or switching to a lighter model in config/victor.yaml will resolve this.)*"
                    
                    return LLMResponse(
                        content=f"[Ollama Error on model '{active_model}']: {err_msg}{hint}",
                        model=active_model,
                        duration=round(time.perf_counter() - start, 3),
                    )
                data = res.json()
        except httpx.ConnectError:
            return LLMResponse(
                content=f"[Ollama Connection Failed]: Cannot connect to Ollama at {self.api_base}. Ensure Ollama is running.",
                model=active_model,
                duration=round(time.perf_counter() - start, 3),
            )
        except Exception as e:
            return LLMResponse(
                content=f"[Ollama Request Exception]: {str(e)}",
                model=active_model,
                duration=round(time.perf_counter() - start, 3),
            )

        duration = round(time.perf_counter() - start, 3)
        message = data.get("message", {})
        content = message.get("content", "")

        return LLMResponse(
            content=content,
            model=data.get("model", active_model),
            duration=duration,
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
        )

    async def stream(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        active_model = await self.resolve_active_model()
        payload = self._prepare_payload(
            active_model,
            messages,
            system_prompt,
            temperature,
            max_tokens,
            stream=True,
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self.api_base}/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        delta = chunk.get("message", {}).get("content", "")
                        if delta:
                            yield delta
                    except json.JSONDecodeError:
                        continue
