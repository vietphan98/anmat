"""Dòng lệnh: python -m anmat <ảnh|video|thư mục> [tuỳ chọn]."""
import argparse
import os
import sys
import time

import cv2

from .blur import MODES, cover
from .compare import before_after
from .detect import FaceDetector

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VID_EXT = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def process_image(path, det, args):
    img = cv2.imread(path)
    if img is None:
        print(f"Bỏ qua (không đọc được): {path}")
        return
    t = time.time()
    faces = det.detect(img)
    out = cover(img, faces, args.kieu, args.le, args.do_manh)
    base, ext = os.path.splitext(path)
    dst = os.path.join(args.ra or os.path.dirname(path) or ".", os.path.basename(base) + "_anmat" + ext)
    cv2.imwrite(dst, out)
    msg = f"✔ {os.path.basename(path)}: {len(faces)} mặt, {time.time() - t:.2f}s -> {dst}"
    if args.so_sanh:
        cmp_path = os.path.join(os.path.dirname(dst), os.path.basename(base) + "_truoc_sau.jpg")
        cv2.imwrite(cmp_path, before_after(img, out, len(faces)))
        msg += f" (+ {cmp_path})"
    print(msg)


def process_video(path, det, args):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    base = os.path.splitext(os.path.basename(path))[0]
    dst = os.path.join(args.ra or os.path.dirname(path) or ".", base + "_anmat.mp4")
    wr = cv2.VideoWriter(dst, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    n, t, last = 0, time.time(), []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        faces = det.detect(frame)
        # giữ khung cũ 1 frame nếu bị mất để tránh "lộ mặt" chớp nhoáng
        use = faces if faces else last
        wr.write(cover(frame, use, args.kieu, args.le, args.do_manh))
        last = faces
        n += 1
    cap.release()
    wr.release()
    print(f"✔ {os.path.basename(path)}: {n} khung hình, {time.time() - t:.1f}s -> {dst}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="anmat", description="Tự động che mặt người trong ảnh/video, offline.")
    p.add_argument("dau_vao", help="Ảnh, video hoặc thư mục")
    p.add_argument("--kieu", choices=MODES, default="mo", help="mo | pixel | den | emoji (mặc định: mo)")
    p.add_argument("--le", type=float, default=0.25, help="Nới rộng vùng che quanh mặt (mặc định 0.25)")
    p.add_argument("--do-manh", type=float, default=1.0, help="Độ mạnh làm mờ/pixel (mặc định 1.0)")
    p.add_argument("--nguong", type=float, default=0.6, help="Ngưỡng tin cậy nhận diện (0-1)")
    p.add_argument("--so-sanh", action="store_true", help="Xuất thêm ảnh so sánh trước/sau")
    p.add_argument("--ra", help="Thư mục lưu kết quả")
    args = p.parse_args(argv)
    if args.ra:
        os.makedirs(args.ra, exist_ok=True)
    det = FaceDetector(args.nguong)
    src = args.dau_vao
    files = [os.path.join(src, f) for f in sorted(os.listdir(src))] if os.path.isdir(src) else [src]
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in IMG_EXT and "_anmat" not in f and "_truoc_sau" not in f:
            process_image(f, det, args)
        elif ext in VID_EXT and "_anmat" not in f:
            process_video(f, det, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
