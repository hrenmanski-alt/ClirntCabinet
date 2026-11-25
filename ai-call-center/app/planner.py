from __future__ import annotations

import httpx

from .config import settings
from .pricing import PricingEngine, PricingInput
from .tool_registry import tool_registry

_NICHES = {
    "салон": "салон красоты",
    "красот": "салон красоты",
    "магазин": "интернет-магазин",
    "кафе": "кафе / ресторан",
    "ресторан": "кафе / ресторан",
    "строй": "строительные услуги",
    "авто": "автосервис",
    "медиц": "медицинская клиника",
    "образован": "образовательные услуги",
}


class BusinessPlanner:
    """Превращает один промпт в план бизнеса с инструментами и сметой."""

    def __init__(self) -> None:
        self.pricing = PricingEngine()

    @staticmethod
    def detect_niche(prompt: str) -> str:
        text = prompt.lower()
        for key, niche in _NICHES.items():
            if key in text:
                return niche
        return "универсальный бизнес"

    async def plan(self, prompt: str) -> dict:
        niche = self.detect_niche(prompt)
        tools = await tool_registry.search_all(prompt)
        estimate = self.pricing.estimate(PricingInput())

        steps = [
            {"id": 1, "title": f"Проанализировать нишу: {niche}", "module": "BusinessPlanner", "approval": False},
            {"id": 2, "title": "Найти инструменты на GitHub и Hugging Face", "module": "ToolRegistry", "approval": False},
            {"id": 3, "title": "Собрать сайт и подключить Метрику", "module": "SiteBuilder + MetricaService", "approval": False},
            {"id": 4, "title": "Подготовить кампанию в Яндекс Директ", "module": "DirectService", "approval": True},
            {"id": 5, "title": "Создать соцканалы и контент-план", "module": "SocialService", "approval": True},
            {"id": 6, "title": "Назначить ИИ-ведущих каналов", "module": "ContentAgents", "approval": True},
            {"id": 7, "title": "Выбрать хостинг и задеплоить", "module": "DeployService", "approval": True},
            {"id": 8, "title": "Рассчитать цену и окупаемость", "module": "PricingEngine", "approval": False},
            {"id": 9, "title": "Показать результат в личном кабинете", "module": "Portal", "approval": False},
        ]

        if settings.business_planner_llm and settings.brain_is_llm:
            llm_steps = await self._llm_steps(prompt, niche)
            if llm_steps:
                steps = llm_steps

        return {
            "prompt": prompt,
            "niche": niche,
            "steps": steps,
            "tools": tools,
            "estimate": estimate,
            "requires_approval": True,
            "mode": "llm" if settings.business_planner_llm and settings.brain_is_llm else "rules",
        }

    async def _llm_steps(self, prompt: str, niche: str) -> list[dict] | None:
        try:
            async with httpx.AsyncClient(timeout=15.0, proxy=settings.https_proxy or None) as client:
                response = await client.post(
                    f"{settings.openai_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    json={
                        "model": settings.llm_model,
                        "messages": [
                            {"role": "system", "content": "Разбей задачу на 6–10 шагов. Верни только JSON-массив объектов с полями title и module."},
                            {"role": "user", "content": f"Ниша: {niche}. Запрос: {prompt}"},
                        ],
                        "temperature": 0.3,
                    },
                )
                response.raise_for_status()
                import json
                raw = response.json()["choices"][0]["message"]["content"]
                items = json.loads(raw)
                return [
                    {"id": i + 1, "title": str(x.get("title", "")), "module": str(x.get("module", "AI")), "approval": False}
                    for i, x in enumerate(items)
                    if isinstance(x, dict)
                ] or None
        except Exception as exc:
            print(f"[planner] LLM недоступен, используем правила: {exc}")
            return None


business_planner = BusinessPlanner()
