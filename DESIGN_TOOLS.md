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

Только скачанные GIF, ничего не рисуется вручную:

- `assets/rotating_earth.gif` — старый public-domain GIF (Wikimedia Commons / NASA), остался в архиве.
- `assets/hand_rotate_source.gif` — скачанный с Wikimedia Commons GIF «Open Hand Monument, rotating in the wind, May 2017» (CC BY-SA 4.0), 1388 кадров, 240×160.
- `deploy_space/assets/hand_rotate.gif` — оптимизированная копия: 40 кадров, 400×267, ~2 МБ. Используется и как фон, и как источник для Braille.

Скачивание:
```bash
curl -L -f -A "ClirntCabinetBot/1.0 (demo)" \
  -o assets/hand_rotate_source.gif \
  "https://upload.wikimedia.org/wikipedia/commons/b/be/Open_Hand_Monument%2C_rotating_in_the_wind%2C_May_2017.gif"
```

Оптимизация (только ресайз и прореживание кадров, не отрисовка):
```bash
python3 - <<'PY'
from PIL import Image
src = Image.open('assets/hand_rotate_source.gif')
frames = []
for i in range(0, src.n_frames, 35):
    src.seek(i)
    fr = src.convert('RGB').resize((400, 267), Image.Resampling.LANCZOS)
    frames.append(fr.convert('P', palette=Image.ADAPTIVE, colors=64))
frames[0].save('deploy_space/assets/hand_rotate.gif', save_all=True,
               append_images=frames[1:], duration=1050, loop=0,
               optimize=True, disposal=2)
PY
```

Атрибуция: Open Hand Monument, Chandigarh — CC BY-SA 4.0, Wikimedia Commons. Указана в подвале страницы.

## Конвертация

`tools/gif_to_braille.py`:

1. Берёт кадры скачанного GIF.
2. `ImageOps.autocontrast(cutoff=1)` — подъём контраста.
3. gamma настраивается (`--gamma`); для ладони использован `1.35`.
4. Ordered dithering по матрице Байера 4×4.
5. Каждые 2×4 пикселя → один символ Unicode Braille (`U+2800` + биты точек).
6. Результат: `deploy_space/ascii_frames.js` (40 кадров 90×30) и `ascii_sample.txt`.

Запуск:
```bash
python3 tools/gif_to_braille.py --src deploy_space/assets/hand_rotate.gif \
  --cols 90 --limit 48 --gamma 1.35
```

## Где используется

`deploy_space/index.html` — светлая витрина в стиле Apple-рекламы:

- скачанный GIF с вращающейся ладонью на заднем плане: `background-size: cover`, `opacity: .13`, `grayscale(1)`, поверх — белая вуаль для читаемости;
- та же ладонь в Braille-анимации в большой «продуктовой» карточке;
- много воздуха, крупная типографика, тонкая навигация, капсульные кнопки; иконки не рисуются;
- статусы модулей, обе архитектурные схемы, исходный GIF рядом с результатом;
- пауза/воспроизведение кликом и пробелом.

Публикация: `https://huggingface.co/spaces/Garrapov2012/clirntcabinet`.
Прямой адрес приложения: `https://garrapov2012-clirntcabinet.static.hf.space/index.html`.
