# detect_and_plot_edges_erect.py
# ------------------------------------------------------------
# Core utilities for subpixel edge detection and symmetry plotting.
# - No private dataset paths, no __main__ entrypoint.
# - All prints are concise English (no emojis).
# - Matplotlib backend set to "Agg" for headless environments.
# ------------------------------------------------------------

import os
import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from glob import glob
from typing import Optional, List, Tuple


def detect_subpixel_edge_row(row: np.ndarray, threshold: int) -> Optional[float]:
    """
    Detect a rising edge crossing `threshold` within a 1D row using linear interpolation.
    Returns subpixel x (float) or None if no crossing exists.
    """
    for i in range(len(row) - 1):
        v0, v1 = int(row[i]), int(row[i + 1])
        if v0 < threshold <= v1:
            # Linear interpolation between i and i+1
            return i + (threshold - v0) / float(max(v1 - v0, 1))
    return None


def process_tile(tile_path: str, out_dir: str, threshold: int, is_right: bool) -> Tuple[str, int]:
    """
    Process a single tile image:
      - For right tiles, horizontally flip to apply the same rule.
      - For each row, compute subpixel edge x position.
      - Save CSV (y,x_sub) and a visualization with red dots at edge positions.

    Returns
    -------
    (base_name, tile_width)
    """
    img = cv2.imread(tile_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {tile_path}")

    h, w = img.shape
    base = os.path.splitext(os.path.basename(tile_path))[0]

    proc = cv2.flip(img, 1) if is_right else img

    edges: List[Tuple[int, float]] = []
    for y in range(h):
        x_sub = detect_subpixel_edge_row(proc[y, :], threshold)
        if x_sub is not None:
            # Map back to original coordinates if the image was flipped
            if is_right:
                x_sub = (w - 1) - x_sub
            edges.append((y, x_sub))

    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"{base}.csv")
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("y,x_sub\n")
        for y, x in edges:
            f.write(f"{y},{x:.4f}\n")

    vis = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    for y, x in edges:
        cv2.circle(vis, (int(round(x)), y), 2, (0, 0, 255), -1)
    cv2.imwrite(os.path.join(out_dir, f"{base}_vis.png"), vis)

    return base, w


def plot_symmetry(out_dir: str, left_name: str, right_name: str, tile_width: int) -> None:
    """
    Load left/right CSVs (y,x_sub), mirror the right edge, and plot both curves.
    Saves '<left>_<right>_symmetry.png' into out_dir.
    """
    import pandas as pd
    dfL = pd.read_csv(os.path.join(out_dir, f"{left_name}.csv"))
    dfR = pd.read_csv(os.path.join(out_dir, f"{right_name}.csv"))

    # Mirror right for symmetric comparison
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


def process_erect_dir(erect_dir: str, threshold: int = 128) -> None:
    """
    Process one 'Erect' directory:
      - expects tiles in '<erect_dir>/erect_crops/torso_slices'
      - writes CSV/visualizations into '<erect_dir>/erect_crops/edges'
      - pairs files '*_left.png' with corresponding '*_right.png'
    """
    slices_dir = os.path.join(erect_dir, "erect_crops", "torso_slices")
    out_dir    = os.path.join(erect_dir, "erect_crops", "edges")

    if not os.path.isdir(slices_dir):
        print(f"No 'torso_slices' folder in: {erect_dir}")
        return

    os.makedirs(out_dir, exist_ok=True)
    left_files = sorted(glob(os.path.join(slices_dir, "*_left.png")))
    if not left_files:
        print(f"No '*_left.png' files in: {slices_dir}")
        return

    any_done = False
    for left_path in left_files:
        root = os.path.basename(left_path)[:-9]  # strip '_left.png'
        right_path = os.path.join(slices_dir, f"{root}_right.png")
        if not os.path.isfile(right_path):
            print(f"Pair not found for: {left_path}")
            continue

        left_name, tile_w = process_tile(left_path, out_dir, threshold, is_right=False)
        right_name, _     = process_tile(right_path, out_dir, threshold, is_right=True)
        plot_symmetry(out_dir, left_name, right_name, tile_w)

        print(f"Processed pair: {os.path.basename(left_path)} | {os.path.basename(right_path)}")
        any_done = True

    if any_done:
        print(f"Done: {erect_dir}")
    else:
        print(f"No pairs processed in: {erect_dir}")
