# Дизайн-конвейер: GIF → символы

## Что скачано и установлено

- **Pillow** 13.0.0 — работа с GIF и кадрами.
- **NumPy** 2.5.4 — матрицы яркости и ordered dithering.
- **imageio** 2.38.2 + **imageio-ffmpeg** 0.8.2 — видео/кадры при необходимости.
- **pyfiglet** 1.0.4 — ASCII-логотип в подвале страницы.
- **rich** 15.0.0 — терминальная проверка/отладка.

Установка: `python3 -m pip install --user --break-system-packages imageio imageio-ffmpeg pyfiglet rich`.

**Важно:** код из случайных GitHub-репозиториев не скачивался и не исполнялся. Использованы только проверенные пакеты из PyPI.

## Источник GIF

`assets/rotating_earth.gif` — вращающаяся Земля, Wikimedia Commons / NASA, public domain.

Скачано:
```bash
curl -L -f -o assets/rotating_earth.gif \
  "https://upload.wikimedia.org/wikipedia/commons/2/2c/Rotating_earth_%28large%29.gif"
```

## Конвертация

`tools/gif_to_braille.py`:

1. Берёт каждый из 44 кадров.
2. `ImageOps.autocontrast(cutoff=1)` — подъём контраста тёмного GIF.
3. gamma `0.65` — вытягивание деталей на Земле.
4. Ordered dithering по матрице Байера 4×4.
5. Каждые 2×4 пикселя → один символ Unicode Braille (`U+2800` + биты точек).
6. Результат: `deploy_space/ascii_frames.js` (44 кадра 84×42) и `ascii_sample.txt`.

## Где используется

`deploy_space/index.html` — неоновая витрина в стиле терминала:

- анимированная Земля из Braille-символов;
- глитч-заголовок, scanlines, шум, sweeping-блик;
- телеметрия, карточки статусов, обе архитектурные схемы;
- исходный GIF рядом с результатом конвертации;
- пауза/воспроизведение кликом и пробелом.

Публикация: `https://huggingface.co/spaces/Garrapov2012/clirntcabinet`.
Прямой адрес приложения: `https://garrapov2012-clirntcabinet.static.hf.space/index.html`.
