# Зарубежный сервер и прокси — как подключить

## Зачем

Прямой запрос к `api.openai.com` из нашего окружения вернул:

```text
HTTP 403 unsupported_country_region_territory
```

Ключ вставлен правильно — проблема в регионе исходящего IP. Решение: VPS за рубежом + HTTP-прокси.

## 1. Выбор VPS

Подойдёт любой маленький сервер за рубежом:

| Провайдер | Локация | Ориентир |
|-----------|---------|----------|
| Timeweb Cloud | Амстердам и др. | удобная оплата из РФ |
| Hetzner | Германия, Финляндия | дёшево, надёжно |
| Vultr / DigitalOcean | Европа/США | классика |
| Oracle Cloud | Always Free | бесплатно, но ARM и квоты |

Минимум: 1 CPU / 1 GB RAM, Ubuntu 22.04+.

## 2. Поднять прокси (tinyproxy)

На сервере:

```bash
apt update && apt install -y tinyproxy
nano /etc/tinyproxy/tinyproxy.conf
```

Измените:

```text
Port 3128
Listen 0.0.0.0
Allow 0.0.0.0/0
BasicAuth proxy_user strong_password
```

Перезапустите:

```bash
systemctl restart tinyproxy
systemctl enable tinyproxy
```

Откройте порт 3128 в файрволе провайдера / `ufw allow 3128/tcp`.

> Лучше ограничить `Allow` конкретным IP нашего сервера, чтобы прокси не стал публичным.

## 3. Альтернатива — SSH-туннель

Без установки прокси-сервера:

```bash
ssh -D 1080 -N -o ServerAliveInterval=60 root@VPS_IP
```

Пот нужен SOCKS5. В `.env` можно указать:

```dotenv
HTTPS_PROXY=socks5://user:pass@VPS_IP:1080
```

Для SOCKS5 в Python нужно: `pip install "httpx[socks]"`.

## 4. Подключить у нас

В файле `ai-call-center/.env`:

```dotenv
HTTPS_PROXY=http://proxy_user:strong_password@VPS_IP:3128
OPENAI_BASE_URL=https://api.openai.com/v1
AI_CALL_MODE=openai
```

Перезапустите сервер. Проверка:

```bash
python3 - <<'PY'
import httpx
from app.config import settings
r = httpx.get(settings.openai_base_url + '/models',
              headers={'Authorization': 'Bearer ' + settings.openai_api_key},
              proxy=settings.https_proxy or None, timeout=20)
print(r.status_code)
PY
```

Ожидаемо: `200`. Если снова `403` — провайдер блокирует датацентр-IP; тогда нужен residential proxy или смена провайдера/локации.

## 5. Что ещё даёт сервер

- прокси для GitHub / Hugging Face API;
- место под деплой кабинета (Nginx + Docker);
- хранилище бэкапов базы;
- в будущем — шлюз Asterisk/FreeSWITCH для Novofon (тут лучше европейский сервер без задержек до РФ).

## Безопасность

- Не публикуйте прокси без BasicAuth — его сразу найдут и начнут злоупотреблять.
- Логин/пароль и IP храните только в `.env`, не в git.
- root-доступ к VPS лучше не пересылать в чат; пришлите готовую строку прокси.
