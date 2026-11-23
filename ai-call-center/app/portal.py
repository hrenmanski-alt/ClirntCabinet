from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from . import db

router = APIRouter()


class _CompatTemplates(Jinja2Templates):
    """Поддержка старого вызова TemplateResponse(name, context) в новых версиях Starlette."""

    def TemplateResponse(self, name: str, context: dict, *args, **kwargs):
        return super().TemplateResponse(
            request=context["request"], name=name, context=context, *args, **kwargs
        )


templates = _CompatTemplates(directory=str(Path(__file__).parent / "templates"))

COOKIE = "cc_session"

RECIPES: list[dict] = [
    {
        "slug": "site-and-telegram",
        "title": "Сайт + заявки в Telegram",
        "description": "Готовый сайт для вашей компании, а все заявки сразу приходят вам в Telegram. Ничего не нужно настраивать.",
        "price": 990,
        "icon": "🌐",
        "fields": [
            {"name": "company", "label": "Название компании", "placeholder": "Салон красоты «Ромашка»"},
            {"name": "city", "label": "Город", "placeholder": "Москва"},
            {"name": "phone", "label": "Ваш телефон", "placeholder": "+7 999 123-45-67"},
        ],
    },
    {
        "slug": "ai-calls",
        "title": "AI-звонки по вашей базе",
        "description": "ИИ сам обзванивает клиентов, отвечает на вопросы и записывает заинтересованных. Вы получаете готовые заявки.",
        "price": 1490,
        "icon": "📞",
        "fields": [
            {"name": "topic", "label": "О чём звонить", "placeholder": "Напоминание о записи"},
            {"name": "base", "label": "Откуда база клиентов", "placeholder": "Excel-файл / из сайта"},
            {"name": "time", "label": "Когда звонить", "placeholder": "По будням с 10 до 18"},
        ],
    },
    {
        "slug": "reminders",
        "title": "Напоминания клиентам",
        "description": "Автоматические напоминания о записи, оплате или встрече — в Telegram и по телефону. Меньше пропущенных визитов.",
        "price": 690,
        "icon": "⏰",
        "fields": [
            {"name": "event", "label": "О чём напоминать", "placeholder": "О записи в салон"},
            {"name": "when", "label": "За сколько напоминать", "placeholder": "За 1 день"},
        ],
    },
    {
        "slug": "autoanswer",
        "title": "Автоответ на вопросы",
        "description": "ИИ отвечает на типовые вопросы клиентов 24/7 и передаёт вам только сложные случаи.",
        "price": 890,
        "icon": "💬",
        "fields": [
            {"name": "questions", "label": "Какие вопросы задают чаще всего", "placeholder": "Цены, часы работы, адрес"},
            {"name": "channel", "label": "Где отвечать", "placeholder": "Telegram / сайт"},
        ],
    },
    {
        "slug": "leads",
        "title": "Сбор заявок с сайта",
        "description": "Ловим заявки с сайта, распределяем по менеджерам и ничего не теряем. Всё видно в одном окне.",
        "price": 790,
        "icon": "🎯",
        "fields": [
            {"name": "source", "label": "Откуда идут заявки", "placeholder": "Форма на сайте"},
            {"name": "where", "label": "Куда их отправлять", "placeholder": "Telegram-канал"},
        ],
    },
]

TEMPLATES: dict[str, dict] = {
    "beauty": {"title": "Салон красоты", "description": "Запись онлайн, услуги и цены"},
    "shop": {"title": "Интернет-магазин", "description": "Каталог товаров и оформление заказа"},
    "service": {"title": "Сервисная компания", "description": "Услуги, цены и заявка на выезд"},
}


def _user(request: Request):
    return db.get_session_user(request.cookies.get(COOKIE))


def _need_user(request: Request):
    user = _user(request)
    if not user:
        return None, RedirectResponse("/login", status_code=302)
    return user, None


@router.get("/", include_in_schema=False)
def index(request: Request):
    if _user(request):
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/login", status_code=302)


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...)):
    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": "Пароль слишком короткий — минимум 6 символов"}
        )
    user_id = db.create_user(email, password)
    if not user_id:
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": "Этот email уже зарегистрирован"}
        )
    token = db.create_session(user_id)
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie(COOKIE, token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return response


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = db.get_user_by_email(email)
    if not user or not db.verify_password(password, user["salt"], user["password_hash"]):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Неверный email или пароль"}
        )
    token = db.create_session(user["id"])
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie(COOKIE, token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return response


@router.post("/logout", include_in_schema=False)
def logout(request: Request):
    db.delete_session(request.cookies.get(COOKIE))
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(COOKIE)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user, redirect = _need_user(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "stats": db.stats(user["id"]), "recipes": RECIPES[:3]},
    )


@router.get("/catalog", response_class=HTMLResponse)
def catalog(request: Request):
    user, redirect = _need_user(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        "catalog.html", {"request": request, "user": user, "recipes": RECIPES, "templates": TEMPLATES}
    )


@router.get("/catalog/{slug}", response_class=HTMLResponse)
def recipe_page(request: Request, slug: str):
    user, redirect = _need_user(request)
    if redirect:
        return redirect
    recipe = next((r for r in RECIPES if r["slug"] == slug), None)
    if not recipe:
        return RedirectResponse("/catalog", status_code=302)
    return templates.TemplateResponse("recipe.html", {"request": request, "user": user, "recipe": recipe})


@router.post("/catalog/{slug}", response_class=HTMLResponse)
async def recipe_submit(request: Request, slug: str):
    user, redirect = _need_user(request)
    if redirect:
        return redirect
    recipe = next((r for r in RECIPES if r["slug"] == slug), None)
    if not recipe:
        return RedirectResponse("/catalog", status_code=302)
    form = await request.form()
    config = {f["name"]: str(form.get(f["name"], "")).strip() for f in recipe["fields"]}
    workflow_id = db.create_workflow(user["id"], slug, recipe["title"], config)
    db.create_invoice(user["id"], recipe["price"], recipe["title"])
    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "user": user,
            "title": "Готово! Автоматизация создана",
            "message": f"«{recipe['title']}» добавлена в ваш кабинет. Оплатите её в разделе «Счета и оплата» — и мы запустим решение.",
            "link": "/billing",
            "link_text": "Перейти к оплате",
        },
    )


@router.get("/sites/new", response_class=HTMLResponse)
def new_site(request: Request):
    user, redirect = _need_user(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        "sites_new.html", {"request": request, "user": user, "templates": TEMPLATES}
    )


@router.post("/sites/new", response_class=HTMLResponse)
async def new_site_submit(request: Request):
    user, redirect = _need_user(request)
    if redirect:
        return redirect
    form = await request.form()
    template = str(form.get("template", "beauty"))
    title = str(form.get("title", "Мой сайт")).strip() or "Мой сайт"
    data = {key: str(value).strip() for key, value in form.items() if key not in ("template", "title")}
    site_id = db.create_site(user["id"], template, title, data)
    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "user": user,
            "title": "Сайт создан",
            "message": f"«{title}» сохранён в вашем кабинете. Мы подготовим публикацию на отдельном адресе.",
            "link": "/dashboard",
            "link_text": "В личный кабинет",
        },
    )


@router.get("/billing", response_class=HTMLResponse)
def billing(request: Request):
    user, redirect = _need_user(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        "billing.html", {"request": request, "user": user, "invoices": db.list_invoices(user["id"])}
    )


@router.post("/billing/{invoice_id}/pay")
def pay(request: Request, invoice_id: int):
    user, redirect = _need_user(request)
    if redirect:
        return redirect
    db.pay_invoice(invoice_id, user["id"])
    return RedirectResponse("/billing", status_code=302)
