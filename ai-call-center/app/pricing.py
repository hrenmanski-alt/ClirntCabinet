from __future__ import annotations

from dataclasses import dataclass

from .config import settings


@dataclass
class PricingInput:
    setup_hours: float = 8.0
    monthly_tools_cost: float = 1500.0
    ad_budget: float = 10000.0
    expected_leads: int = 60
    conversion_rate: float = 0.15
    avg_deal: float = 5000.0
    margin: float = 0.30


class PricingEngine:
    """Считает себестоимость, рекомендованную цену и окупаемость."""

    def estimate(self, data: PricingInput) -> dict[str, float | str | bool]:
        rate = float(settings.hourly_rate)
        setup_cost = data.setup_hours * rate
        one_time_cost = setup_cost + data.ad_budget
        monthly_cost = data.monthly_tools_cost + data.ad_budget

        expected_revenue = data.expected_leads * data.conversion_rate * data.avg_deal
        gross_profit = expected_revenue - monthly_cost
        recommended_price = one_time_cost * (1 + data.margin) + monthly_cost
        payback_months = recommended_price / max(gross_profit, 1.0)
        viable = payback_months <= 3.0

        return {
            "setup_cost": round(setup_cost, 2),
            "one_time_cost": round(one_time_cost, 2),
            "monthly_cost": round(monthly_cost, 2),
            "expected_revenue": round(expected_revenue, 2),
            "gross_profit": round(gross_profit, 2),
            "recommended_price": round(recommended_price, 2),
            "payback_months": round(payback_months, 2),
            "viable": viable,
            "verdict": "окупается" if viable else "рискованно: проверьте бюджет и конверсию",
        }


pricing_engine = PricingEngine()
