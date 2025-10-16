# detect_and_plot_edges_erect.py

import os
import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")  # GUI 없는 환경 안전
import matplotlib.pyplot as plt
from glob import glob

def detect_subpixel_edge_row(row: np.ndarray, threshold: int):
    for i in range(len(row) - 1):
        v0, v1 = int(row[i]), int(row[i + 1])
        if v0 < threshold <= v1:
            return i + (threshold - v0) / float(v1 - v0)
    return None

def process_tile(tile_path: str, out_dir: str, threshold: int, is_right: bool):
    img = cv2.imread(tile_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(tile_path)
    h, w = img.shape
    base = os.path.splitext(os.path.basename(tile_path))[0]

    # 오른쪽 타일은 좌우 반전해서 동일 규칙 적용
    proc = cv2.flip(img, 1) if is_right else img

    edges = []
    for y in range(h):
        x_sub = detect_subpixel_edge_row(proc[y, :], threshold)
        if x_sub is not None:
            if is_right:
                x_sub = (w - 1) - x_sub  # 원래 좌표계로 복원
            edges.append((y, x_sub))

    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"{base}.csv")
    with open(csv_path, 'w') as f:
        f.write("y,x_sub\n")
        for y, x in edges:
            f.write(f"{y},{x:.4f}\n")

    vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    for y, x in edges:
        cv2.circle(vis, (int(round(x)), y), 2, (0, 0, 255), -1)
    cv2.imwrite(os.path.join(out_dir, f"{base}_vis.png"), vis)

    return base, w

def plot_symmetry(out_dir: str, left_name: str, right_name: str, tile_width: int):
    import pandas as pd
    import os as _os
    dfL = pd.read_csv(_os.path.join(out_dir, f"{left_name}.csv"))
    dfR = pd.read_csv(_os.path.join(out_dir, f"{right_name}.csv"))
    # 대칭 비교 위해 오른쪽 반사
    dfR['x_sub'] = (tile_width - 1) - dfR['x_sub']

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(dfL['y'], dfL['x_sub'], '-o', ms=3, label='Left')
    ax.plot(dfR['y'], dfR['x_sub'], '-o', ms=3, label='Right (mirrored)')
    ax.set_xlabel("Row (y)")
    ax.set_ylabel("Subpixel x")
    ax.set_title("Symmetric Edge Comparison")
    ax.grid(True)
    ax.set_aspect('equal', 'box')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, f"{left_name}_{right_name}_symmetry.png"), dpi=200)
    plt.close()

def process_erect_dir(erect_dir: str, threshold: int = 128):
    slices_dir = os.path.join(erect_dir, "erect_crops", "torso_slices")
    out_dir    = os.path.join(erect_dir, "erect_crops", "edges")

    if not os.path.isdir(slices_dir):
        print(f"⚠️  No torso_slices folder in {erect_dir}")
        return

    os.makedirs(out_dir, exist_ok=True)
    left_files = sorted(glob(os.path.join(slices_dir, "*_left.png")))
    if not left_files:
        print(f"⚠️  No *_left.png in {slices_dir}")
        return

    any_done = False
    for left_path in left_files:
        root = os.path.basename(left_path)[:-9]  # "_left.png" 제거
        right_path = os.path.join(slices_dir, f"{root}_right.png")
        if not os.path.isfile(right_path):
            print(f"⚠️  Pair not found for: {left_path}")
            continue

        left_name, tile_w = process_tile(left_path, out_dir, threshold, is_right=False)
        right_name, _     = process_tile(right_path, out_dir, threshold, is_right=True)
        plot_symmetry(out_dir, left_name, right_name, tile_w)

        print(f"✅ Processed pair: {os.path.basename(left_path)} | {os.path.basename(right_path)}")
        any_done = True

    print("✔ Done:" if any_done else "⚠️  No pairs processed in", erect_dir)

def main():
    BASE_ROOT = r"C:\Users\f0r2o\PycharmProjects\XRAYSCO\8_8"
    FIRST_PID = 24
    LAST_PID  = 30
    THRESHOLD = 128

    for pid in range(FIRST_PID, LAST_PID + 1):
        erect_dir = os.path.join(BASE_ROOT, f"P{pid:03d}", "Erect")
        if not os.path.isdir(erect_dir):
            print(f"⚠️  Missing: {erect_dir}")
            continue
        print(f"--- Edge detection for P{pid:03d} ---")
        try:
            process_erect_dir(erect_dir, threshold=THRESHOLD)
        except Exception as e:
            print(f"❌ Error in {erect_dir}: {e}")

if __name__ == "__main__":
    main()
