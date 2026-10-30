"""Các kiểu che mặt: mờ, pixel, hộp đen, emoji."""
import cv2
import numpy as np

MODES = ("mo", "pixel", "den", "emoji")


def _expand(box, shape, pad):
    x, y, w, h = box
    H, W = shape[:2]
    dx, dy = int(w * pad), int(h * pad)
    x0, y0 = max(0, x - dx), max(0, y - dy)
    x1, y1 = min(W, x + w + dx), min(H, y + h + dy)
    return x0, y0, x1, y1


def _ellipse_mask(hh, ww):
    mask = np.zeros((hh, ww), np.uint8)
    cv2.ellipse(mask, (ww // 2, hh // 2), (ww // 2, hh // 2), 0, 0, 360, 255, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), max(1, min(hh, ww) / 20))
    return (mask.astype(np.float32) / 255.0)[..., None]


def _smiley(size):
    s = size
    img = np.zeros((s, s, 3), np.uint8)
    c, r = s // 2, s // 2 - 1
    cv2.circle(img, (c, c), r, (40, 210, 255), -1, cv2.LINE_AA)
    cv2.circle(img, (c, c), r, (20, 140, 200), max(1, s // 40), cv2.LINE_AA)
    eye = max(2, s // 12)
    cv2.circle(img, (int(c - s * 0.17), int(c - s * 0.1)), eye, (40, 40, 40), -1, cv2.LINE_AA)
    cv2.circle(img, (int(c + s * 0.17), int(c - s * 0.1)), eye, (40, 40, 40), -1, cv2.LINE_AA)
    cv2.ellipse(img, (c, int(c + s * 0.05)), (int(s * 0.25), int(s * 0.2)), 0, 20, 160,
                (40, 40, 40), max(2, s // 25), cv2.LINE_AA)
    return img


def cover(img, boxes, mode="mo", pad=0.25, strength=1.0):
    out = img.copy()
    for box in boxes:
        x0, y0, x1, y1 = _expand(box, img.shape, pad)
        ww, hh = x1 - x0, y1 - y0
        if ww < 4 or hh < 4:
            continue
        roi = out[y0:y1, x0:x1]
        if mode == "pixel":
            blocks = max(3, int(8 / strength))  # số ô pixel theo chiều ngang của mặt
            bh = max(3, int(blocks * hh / ww))
            small = cv2.resize(roi, (blocks, bh), interpolation=cv2.INTER_AREA)
            new = cv2.resize(small, (ww, hh), interpolation=cv2.INTER_NEAREST)
            out[y0:y1, x0:x1] = new
            continue
        if mode == "den":
            cv2.rectangle(out, (x0, y0), (x1, y1), (0, 0, 0), -1)
            continue
        if mode == "emoji":
            s = max(ww, hh)
            face = _smiley(s)
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            fx0, fy0 = cx - s // 2, cy - s // 2
            H, W = out.shape[:2]
            ax0, ay0, ax1, ay1 = max(0, fx0), max(0, fy0), min(W, fx0 + s), min(H, fy0 + s)
            sub = face[ay0 - fy0:ay1 - fy0, ax0 - fx0:ax1 - fx0]
            m = np.zeros(face.shape[:2], np.uint8)
            cv2.circle(m, (s // 2, s // 2), s // 2 - 1, 255, -1, cv2.LINE_AA)
            m = (m[ay0 - fy0:ay1 - fy0, ax0 - fx0:ax1 - fx0].astype(np.float32) / 255)[..., None]
            dst = out[ay0:ay1, ax0:ax1].astype(np.float32)
            out[ay0:ay1, ax0:ax1] = (sub * m + dst * (1 - m)).astype(np.uint8)
            continue
        # mặc định: làm mờ mạnh theo hình elip, viền mềm
        k = int(max(ww, hh) * 0.35 * strength) | 1
        blurred = cv2.GaussianBlur(roi, (k, k), 0)
        blurred = cv2.GaussianBlur(blurred, (k, k), 0)
        m = _ellipse_mask(hh, ww)
        out[y0:y1, x0:x1] = (blurred * m + roi * (1 - m)).astype(np.uint8)
    return out
