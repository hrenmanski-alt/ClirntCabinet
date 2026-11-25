from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import db
from .planner import business_planner
from .pricing import PricingEngine, PricingInput
from .tool_registry import tool_registry

router = APIRouter()
COOKIE = "cc_session"


class PlanRequest(BaseModel):
    prompt: str


class PricingRequest(BaseModel):
    setup_hours: float = 8.0
    monthly_tools_cost: float = 1500.0
    ad_budget: float = 10000.0
    expected_leads: int = 60
    conversion_rate: float = 0.15
    avg_deal: float = 5000.0
    margin: float = 0.30


def _user(request: Request):
    return db.get_session_user(request.cookies.get(COOKIE))


@router.post("/api/business/plan")
async def create_plan(request: Request, payload: PlanRequest):
    if not _user(request):
        return JSONResponse({"detail": "Нужно войти в аккаунт"}, status_code=401)
    if not payload.prompt.strip():
        return JSONResponse({"detail": "Промпт пустой"}, status_code=400)
    plan = await business_planner.plan(payload.prompt.strip())
    return {"ok": True, **plan}


@router.get("/api/tools/search")
async def search_tools(request: Request, query: str = ""):
    if not _user(request):
        return JSONResponse({"detail": "Нужно войти в аккаунт"}, status_code=401)
    tools = await tool_registry.search_all(query)
    return {"ok": True, "query": query, "tools": tools}


@router.post("/api/pricing/estimate")
def estimate_price(request: Request, payload: PricingRequest):
    if not _user(request):
        return JSONResponse({"detail": "Нужно войти в аккаунт"}, status_code=401)
    data = PricingInput(**payload.model_dump())
    return {"ok": True, **PricingEngine().estimate(data)}
