# Дизайн-конвейер: GIF → символы

## Что скачано и установлено

- **Pillow** 13.0.0 — работа с GIF и кадрами.
- **NumPy** 2.5.4 — матрицы яркости и ordered dithering.
- **imageio** 2.38.2 + **imageio-ffmpeg** 0.8.2 — видео/кадры при необходимости.
- **pyfiglet** 1.0.4 — ASCII-логотип в подвале страницы.
- **rich** 15.0.0 — терминальная проверка/отладка.

Установка: `python3 -m pip install --user --break-system-packages imageio imageio-ffmpeg pyfiglet rich`.

**Важно:** код из случайных GitHub-репозиториев не скачивался и не исполнялся. Использованы только проверенные пакеты из PyPI.

## Источники GIF

- `assets/rotating_earth.gif` — скачанный public-domain GIF (Wikimedia Commons / NASA). Остался в архиве как пример «старого» источника.
- `assets/neon_flow.gif` — новый источник для витрины: абстрактная неоновая волна без космической тематики. Сгенерирован `tools/make_neon_gif.py` (480×270, 48 кадров).

Скачивание исходного GIF:
```bash
curl -L -f -o assets/rotating_earth.gif \
  "https://upload.wikimedia.org/wikipedia/commons/2/2c/Rotating_earth_%28large%29.gif"
```

Генерация нового GIF:
```bash
python3 tools/make_neon_gif.py
```

## Конвертация

`tools/gif_to_braille.py`:

1. Берёт каждый из 44 кадров.
2. `ImageOps.autocontrast(cutoff=1)` — подъём контраста тёмного GIF.
3. gamma настраивается (`--gamma`); для неоновой волны использован `2.7`, чтобы остались тёмные промежутки.
4. Ordered dithering по матрице Байера 4×4.
5. Каждые 2×4 пикселя → один символ Unicode Braille (`U+2800` + биты точек).
6. Результат: `deploy_space/ascii_frames.js` (48 кадров 90×25) и `ascii_sample.txt`.

Запуск:
```bash
python3 tools/gif_to_braille.py --cols 90 --limit 48 --gamma 2.7
```

## Где используется

`deploy_space/index.html` — современная светлая витрина в белом стиле:

- анимированная неоновая волна из Braille-символов в стеклянной карточке;
- **вращающаяся рука** на заднем плане: встроенный SVG с градиентной заливкой, медленное вращение 34 с, пониженная прозрачность, отключение при `prefers-reduced-motion`;
- белый фон с мягкими пастельными радиальными градиентами, тонкая сетка, большая типографика, скруглённые карточки;
- градиентный заголовок, статистика, статусы модулей, обе архитектурные схемы;
- исходный GIF рядом с результатом конвертации;
- пауза/воспроизведение кликом и пробелом.

Публикация: `https://huggingface.co/spaces/Garrapov2012/clirntcabinet`.
Прямой адрес приложения: `https://garrapov2012-clirntcabinet.static.hf.space/index.html`.
