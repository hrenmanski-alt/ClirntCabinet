"""Generate a modern neon-plasma GIF (no space theme) for the Braille pipeline."""

from __future__ import annotations

import numpy as np
from PIL import Image

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "neon_flow.gif"

W, H, FRAMES = 480, 270, 48


def main() -> None:
    x = np.linspace(-1.6, 1.6, W, dtype=np.float32)
    y = np.linspace(-0.9, 0.9, H, dtype=np.float32)
    X, Y = np.meshgrid(x, y)
    r = np.sqrt(X * X + Y * Y)

    images: list[Image.Image] = []
    for k in range(FRAMES):
        t = 2 * np.pi * k / FRAMES
        wave = 0.5 + 0.5 * np.sin(5 * X + 3 * Y + 3 * t + 1.5 * np.sin(2 * Y - t))
        ring = np.exp(-6 * (r - (0.55 + 0.12 * np.sin(2 * t))) ** 2)
        flow = 0.5 + 0.5 * np.sin(7 * (X * 0.7 + Y * 0.9) - 4 * t)
        glow = np.exp(-2.2 * r)

        v = np.clip(0.34 * wave + 0.42 * ring + 0.24 * flow + 0.28 * glow, 0, 1)

        # modern palette: violet -> cyan -> pink
        c1 = np.array([80, 40, 200], dtype=np.float32)    # violet
        c2 = np.array([30, 230, 255], dtype=np.float32)   # cyan
        c3 = np.array([255, 60, 200], dtype=np.float32)   # pink
        m = np.clip(v * 2, 0, 1)[..., None]
        n = np.clip(v * 2 - 1, 0, 1)[..., None]
        rgb = c1 * (1 - m) + c2 * m * (1 - n) + c3 * m * n
        rgb *= 0.35 + 0.75 * v[..., None]
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)

        images.append(Image.fromarray(rgb, "RGB"))

    images[0].save(OUT, save_all=True, append_images=images[1:], duration=80, loop=0, optimize=False)
    print("saved", OUT, W, "x", H, FRAMES, "frames")


if __name__ == "__main__":
    main()
