"""Ghép ảnh so sánh TRƯỚC / SAU có chữ tiếng Việt."""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/sand-box/google/Be Vietnam Pro/BeVietnamPro-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def _font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _label(pil, text, color):
    d = ImageDraw.Draw(pil)
    f = _font(max(22, pil.width // 18))
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    pad = 14
    d.rounded_rectangle((16, 16, 16 + r - l + 2 * pad, 16 + b - t + 2 * pad), 12, fill=color)
    d.text((16 + pad - l, 16 + pad - t), text, font=f, fill="white")


def before_after(before, after, n_faces, title=None):
    h = 900
    def fit(img):
        s = h / img.shape[0]
        return cv2.resize(img, (int(img.shape[1] * s), h), interpolation=cv2.INTER_AREA)
    a = Image.fromarray(cv2.cvtColor(fit(before), cv2.COLOR_BGR2RGB))
    b = Image.fromarray(cv2.cvtColor(fit(after), cv2.COLOR_BGR2RGB))
    _label(a, "TRƯỚC", (200, 40, 40))
    _label(b, f"SAU: đã che {n_faces} khuôn mặt", (30, 140, 70))
    gap = 12
    head = 110
    canvas = Image.new("RGB", (a.width + b.width + gap, h + head), (18, 18, 22))
    canvas.paste(a, (0, head))
    canvas.paste(b, (a.width + gap, head))
    d = ImageDraw.Draw(canvas)
    f = _font(52)
    text = title or "Che mặt tự động – chạy offline"
    l, t, r, bb = d.textbbox((0, 0), text, font=f)
    d.text(((canvas.width - (r - l)) // 2 - l, (head - (bb - t)) // 2 - t), text, font=f, fill="white")
    return cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR)
