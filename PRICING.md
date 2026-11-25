# Ценообразование и окупаемость — ветка `feature/pricing`

## Модель

Реализована в `app/pricing.py` на ветке `feature/agent-hub`, сюда будет перенесена после слияния.

```text
setup_cost      = часы настройки × HOURLY_RATE
one_time_cost   = setup_cost + рекламный бюджет
monthly_cost    = инструменты + рекламный бюджет
expected_revenue= лиды × конверсия × средний чек
recommended_price = one_time_cost × (1 + маржа) + monthly_cost
payback_months  = recommended_price / прибыль в месяц
```

Если окупаемость больше 3 месяцев — вердикт «рискованно», нужно снижать бюджет или повышать конверсию.

## Endpoint

```http
POST /api/pricing/estimate
{
  "setup_hours": 8,
  "monthly_tools_cost": 1500,
  "ad_budget": 10000,
  "expected_leads": 60,
  "conversion_rate": 0.15,
  "avg_deal": 5000,
  "margin": 0.30
}
```

## Что дальше

- тарифы на сайты, звонки, соцсети и рекламу;
- автоматический пересчёт цены при изменении бюджета;
- отчёт «окупается / не окупается» в личном кабинете.
