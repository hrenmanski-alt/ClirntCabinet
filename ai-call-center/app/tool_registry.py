from __future__ import annotations

import re
from typing import Any

import httpx

from .config import settings

# Проверенный allowlist: это то, что мы безопасно рекомендуем и используем
# как метаданные. Произвольный код из найденных репозиториев НЕ выполняется.
CURATED_GITHUB: list[dict[str, Any]] = [
    {"name": "fastapi/fastapi", "description": "Быстрый API на Python", "url": "https://github.com/fastapi/fastapi"},
    {"name": "langchain-ai/langchain", "description": "Оркестрация LLM и инструментов", "url": "https://github.com/langchain-ai/langchain"},
    {"name": "n8n-io/n8n", "description": "Автоматизации и рабочие процессы", "url": "https://github.com/n8n-io/n8n"},
    {"name": "huggingface/transformers", "description": "Модели и Inference", "url": "https://github.com/huggingface/transformers"},
    {"name": "openai/openai-python", "description": "Клиент OpenAI API", "url": "https://github.com/openai/openai-python"},
    {"name": "python-telegram-bot/python-telegram-bot", "description": "Telegram-боты", "url": "https://github.com/python-telegram-bot/python-telegram-bot"},
]

CURATED_HF: list[dict[str, Any]] = [
    {"name": "sberbank-ai/rugpt3small_based_on_gpt2", "description": "Русскоязычная генерация текста", "url": "https://huggingface.co/sberbank-ai/rugpt3small_based_on_gpt2"},
    {"name": "cointegrated/rut5-base", "description": "Русскоязычный T5", "url": "https://huggingface.co/cointegrated/rut5-base"},
    {"name": "sberbank-ai/sbert_large_nlu_ru", "description": "Русские эмбеддинги", "url": "https://huggingface.co/sberbank-ai/sbert_large_nlu_ru"},
]

KEYWORD_QUERIES = {
    "site": "website builder python",
    "ad": "yandex direct api advertising",
    "social": "social media automation telegram bot",
    "analytics": "web analytics metrics",
    "voice": "speech recognition russian tts",
    "deploy": "deployment hosting automation",
}


class GitHubToolRegistry:
    BASE = "https://api.github.com"

    def _client(self) -> httpx.Client:
        headers = {"Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        return httpx.Client(timeout=12.0, headers=headers, proxy=settings.https_proxy or None)

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not query.strip():
            return [dict(x, source="github") for x in CURATED_GITHUB[:limit]]
        try:
            with self._client() as client:
                response = client.get(
                    f"{self.BASE}/search/repositories",
                    params={"q": query, "sort": "stars", "per_page": limit},
                )
                response.raise_for_status()
                items = response.json().get("items", [])
            return [
                {
                    "name": item["full_name"],
                    "description": item.get("description") or "",
                    "url": item["html_url"],
                    "stars": item.get("stargazers_count", 0),
                    "source": "github",
                }
                for item in items
            ]
        except Exception as exc:
            print(f"[registry] GitHub search failed: {exc}")
            return [dict(x, source="github") for x in CURATED_GITHUB[:limit]]


class HuggingFaceToolRegistry:
    BASE = "https://huggingface.co/api"

    def _client(self) -> httpx.Client:
        headers = {}
        if settings.huggingface_token:
            headers["Authorization"] = f"Bearer {settings.huggingface_token}"
        return httpx.Client(timeout=12.0, headers=headers, proxy=settings.https_proxy or None)

    def search_models(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not query.strip():
            return [dict(x, source="huggingface") for x in CURATED_HF[:limit]]
        try:
            with self._client() as client:
                response = client.get(f"{self.BASE}/models", params={"search": query, "limit": limit})
                response.raise_for_status()
                items = response.json()
            return [
                {
                    "name": item.get("modelId", ""),
                    "description": "model",
                    "url": f"https://huggingface.co/{item.get('modelId', '')}",
                    "downloads": item.get("downloads", 0),
                    "source": "huggingface",
                }
                for item in items
            ]
        except Exception as exc:
            print(f"[registry] HF search failed: {exc}")
            return [dict(x, source="huggingface") for x in CURATED_HF[:limit]]


class ToolRegistry:
    """Ищет полезные инструменты, но не выполняет чужой код."""

    def __init__(self) -> None:
        self.github = GitHubToolRegistry()
        self.huggingface = HuggingFaceToolRegistry()

    async def search_all(self, prompt: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        text = prompt.lower()
        for key, query in KEYWORD_QUERIES.items():
            if key in text:
                for tool in self.github.search(query, limit=3):
                    if tool["name"] not in seen:
                        seen.add(tool["name"])
                        results.append(tool)
        if not results:
            results.extend(dict(x, source="github") for x in CURATED_GITHUB[:4])
        results.extend(dict(x, source="huggingface") for x in CURATED_HF[:2])
        return results


tool_registry = ToolRegistry()
