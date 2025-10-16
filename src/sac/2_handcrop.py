# manual_erect_cropping.py
# P024~P030 / Erect / P***_*_E_1.jpg + erect_masks_skin_only/{base}_mask.png 기준 수동 크롭

import os
import cv2
import numpy as np
from glob import glob

# === 기본 설정(필요시 여기만 수정) ===
BASE_ROOT       = r"C:\Users\f0r2o\PycharmProjects\XRAYSCO\8_8"
FIRST_PID       = 24
LAST_PID        = 30
OUT_DIR_NAME    = "erect_crops"
MASK_DIR_NAME   = "erect_masks_skin_only"
SAVE_COLOR_CROP = False          # 원본 컬러도 같이 저장하려면 True
PAD_PX          = 0              # ROI 테두리 여유(패딩) 픽셀
MAX_W, MAX_H    = 1400, 900      # 미리보기 창 최대 크기(화면에 맞게)
OVERLAY_ALPHA   = 0.35           # 오버레이 투명도

WIN = "Erect Cropper — [E] 새 박스  [Y] 이전 박스 재사용  [O] 보기 전환  [S] 건너뜀  [Q/ESC] 종료"

def _find_erect_image(erect_dir: str, pid: int) -> str | None:
    """P{pid:03d}_*_E_1.(jpg/jpeg/JPG/JPEG) 중 첫 번째를 반환."""
    pats = [
        os.path.join(erect_dir, f"P{pid:03d}_*_E_1.jpg"),
        os.path.join(erect_dir, f"P{pid:03d}_*_E_1.jpeg"),
        os.path.join(erect_dir, f"P{pid:03d}_*_E_1.JPG"),
        os.path.join(erect_dir, f"P{pid:03d}_*_E_1.JPEG"),
    ]
    m = []
    for p in pats: m.extend(glob(p))
    m = sorted(m)
    return m[0] if m else None

def _mask_path_for(erect_dir: str, base_no_ext: str) -> str | None:
    p = os.path.join(erect_dir, MASK_DIR_NAME, f"{base_no_ext}_mask.png")
    return p if os.path.isfile(p) else None

def _make_overlay(img_bgr: np.ndarray, mask_gray: np.ndarray, alpha: float=0.35) -> np.ndarray:
    img = img_bgr.copy()
    red = np.zeros_like(img); red[...,2] = 255
    m = mask_gray > 0
    overlay = img.copy()
    overlay[m] = red[m]
    return cv2.addWeighted(overlay, alpha, img, 1-alpha, 0)

def _resize_for_display(img: np.ndarray, max_w: int, max_h: int) -> tuple[np.ndarray, float]:
    h, w = img.shape[:2]
    s = min(max_w / w, max_h / h, 1.0)
    if s < 1.0:
        img = cv2.resize(img, (int(w*s), int(h*s)), interpolation=cv2.INTER_AREA)
    return img, s

def _draw_text(img: np.ndarray, lines: list[str]) -> None:
    y = 24
    for ln in lines:
        cv2.putText(img, ln, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20,20,20), 3, cv2.LINE_AA)
        cv2.putText(img, ln, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)
        y += 22

def _save_crops(mask: np.ndarray, color: np.ndarray, roi_xywh: tuple[int,int,int,int],
                out_dir: str, base: str, pad: int, save_color: bool):
    H, W = mask.shape[:2]
    x, y, w, h = map(int, roi_xywh)
    x0 = max(0, x - pad); y0 = max(0, y - pad)
    x1 = min(W, x + w + pad); y1 = min(H, y + h + pad)

    crop_mask = mask[y0:y1, x0:x1]
    os.makedirs(out_dir, exist_ok=True)
    out_mask_path = os.path.join(out_dir, f"cropped_torso_{base}.png")
    cv2.imwrite(out_mask_path, crop_mask)

    if save_color:
        crop_color = color[y0:y1, x0:x1]
        out_color_path = os.path.join(out_dir, f"cropped_torso_{base}_color.png")
        cv2.imwrite(out_color_path, crop_color)

    print(f"✅ Saved: {out_mask_path}  shape={crop_mask.shape[1]}x{crop_mask.shape[0]}")
    if save_color:
        print(f"✅ Saved: {out_color_path}  shape={crop_color.shape[1]}x{crop_color.shape[0]}")

def main():
    last_roi = None   # (x, y, w, h) — 이전 이미지에서 선택한 ROI 재사용
    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)

    # P024 ~ P030 순회
    for pid in range(FIRST_PID, LAST_PID + 1):
        erect_dir = os.path.join(BASE_ROOT, f"P{pid:03d}", "Erect")
        if not os.path.isdir(erect_dir):
            print(f"⚠️ 폴더 없음: {erect_dir}")
            continue

        img_path = _find_erect_image(erect_dir, pid)
        if not img_path:
            print(f"⚠️ 대상 이미지 없음: {erect_dir}\\P{pid:03d}_*_E_1.jpg")
            continue

        base = os.path.splitext(os.path.basename(img_path))[0]
        mask_path = _mask_path_for(erect_dir, base)
        if not mask_path:
            print(f"⚠️ 마스크 없음: {erect_dir}\\{MASK_DIR_NAME}\\{base}_mask.png")
            continue

        color = cv2.imread(img_path)
        mask  = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if color is None or mask is None:
            print(f"⚠️ 로드 실패: {img_path} / {mask_path}")
            continue

        mode = 0
        overlay = _make_overlay(color, mask, OVERLAY_ALPHA)
        previews = [overlay, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR), color]

        while True:
            view = previews[mode].copy()
            disp, s = _resize_for_display(view, MAX_W, MAX_H)

            msg = [
                f"[P{pid:03d}] {base}",
                "[E] 새 박스  [Y] 이전 박스 재사용  [O] 보기 전환(overlay/mask/color)  [S] 건너뜀  [Q/ESC] 종료",
                "selectROI: ENTER/SPACE 저장, C 취소"
            ]
            if last_roi is not None:
                x, y, w, h = last_roi
                rx, ry, rw, rh = int(x*s), int(y*s), int(w*s), int(h*s)
                cv2.rectangle(disp, (rx, ry), (rx+rw, ry+rh), (0,255,0), 2)
                msg.append(f"이전 ROI: x={x}, y={y}, w={w}, h={h} (재사용: Y)")
            _draw_text(disp, msg)

            cv2.imshow(WIN, disp)
            k = cv2.waitKey(0) & 0xFF

            if k in (ord('o'), ord('O')):
                mode = (mode + 1) % 3
                continue
            if k in (ord('s'), ord('S')):  # skip
                print(f"⏭  Skipped: P{pid:03d}")
                break
            if k in (ord('q'), ord('Q'), 27):  # ESC
                print("👋 종료합니다.")
                cv2.destroyAllWindows()
                return
            if k in (ord('y'), ord('Y')) and last_roi is not None:
                out_dir = os.path.join(erect_dir, OUT_DIR_NAME)
                _save_crops(mask, color, last_roi, out_dir, base, PAD_PX, SAVE_COLOR_CROP)
                break
            if k in (ord('e'), ord('E')) or last_roi is None:
                roi_disp = cv2.selectROI(WIN, disp, showCrosshair=True, fromCenter=False)
                if roi_disp[2] <= 0 or roi_disp[3] <= 0:
                    print("❕ ROI 선택 취소")
                    continue
                # 스케일 보정
                x = int(roi_disp[0] / s); y = int(roi_disp[1] / s)
                w = int(roi_disp[2] / s); h = int(roi_disp[3] / s)
                last_roi = (x, y, w, h)

                out_dir = os.path.join(erect_dir, OUT_DIR_NAME)
                _save_crops(mask, color, last_roi, out_dir, base, PAD_PX, SAVE_COLOR_CROP)
                break

    cv2.destroyAllWindows()
    print("✔ 전체 완료")

if __name__ == "__main__":
    main()
