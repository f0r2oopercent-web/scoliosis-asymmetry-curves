# split_erect_cropped_torso.py

import os
import cv2
from glob import glob

def split_cropped_torso(img_path: str, out_dir: str, n_slices: int = 0):
    """
    그레이스케일 마스크를 좌/우 또는 세로 슬라이스로 분할 저장.
      - n_slices <= 1: 좌/우 두 장 저장8              Z
      - n_slices  > 1: 각 half를 n_slices로 세로 분할
    """
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {img_path}")

    H, W = img.shape
    x_mid = W // 2
    left  = img[:, :x_mid]
    right = img[:, x_mid:]

    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(img_path))[0]

    if n_slices <= 1:
        cv2.imwrite(os.path.join(out_dir, f"{base}_left.png"),  left)
        cv2.imwrite(os.path.join(out_dir, f"{base}_right.png"), right)
        print(f"✅ Saved left/right halves for {base} in {out_dir}")
        return

    slice_h = H // n_slices
    for i in range(n_slices):
        y0 = i * slice_h
        y1 = (i + 1) * slice_h if i < n_slices - 1 else H
        cv2.imwrite(os.path.join(out_dir, f"{base}_left_{i:02d}.png"),  left[y0:y1, :])
        cv2.imwrite(os.path.join(out_dir, f"{base}_right_{i:02d}.png"), right[y0:y1, :])

    print(f"✅ Split {base} into {2 * n_slices} pieces in {out_dir}")

def main():
    # ===== 현재 폴더 구조에 맞춘 설정 =====
    BASE_ROOT = r"C:\Users\f0r2o\PycharmProjects\XRAYSCO\8_8"
    FIRST_PID = 24
    LAST_PID  = 30
    N_SLICES  = 0   # 0이면 좌/우 두 장만 생성, >1이면 세로 슬라이스 수
    # ====================================

    for pid in range(FIRST_PID, LAST_PID + 1):
        erect_dir  = os.path.join(BASE_ROOT, f"P{pid:03d}", "Erect")
        crops_dir  = os.path.join(erect_dir, "erect_crops")
        out_dir    = os.path.join(crops_dir, "torso_slices")

        if not os.path.isdir(crops_dir):
            print(f"⚠️  erect_crops 없음: {crops_dir}")
            continue

        # 컬러 저장본(*_color.png)은 건너뜀
        for img_path in sorted(glob(os.path.join(crops_dir, "cropped_torso_*.png"))):
            if img_path.lower().endswith("_color.png"):
                continue
            try:
                split_cropped_torso(img_path, out_dir, n_slices=N_SLICES)
            except Exception as e:
                print(f"❌ Error on {img_path}: {e}")

    print("✔ 전체 완료")

if __name__ == "__main__":
    main()
