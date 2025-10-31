# split_erect_cropped_torso.py
# ------------------------------------------------------------
# Core utility to split a grayscale torso mask into left/right
# halves or vertical slices. No dataset paths, no __main__.
# ------------------------------------------------------------

import os
import cv2
from glob import glob
from typing import Optional


def split_cropped_torso(img_path: str, out_dir: str, n_slices: int = 0) -> None:
    """
    Split a grayscale mask into left/right halves, or into vertical slices per half.

    Behavior
    --------
    - n_slices <= 1: save two images (left, right)
    - n_slices  > 1: for each half, save n_slices vertical pieces

    Parameters
    ----------
    img_path : str
        Path to the input grayscale mask image.
    out_dir  : str
        Directory to write outputs. Will be created if missing.
    n_slices : int
        Number of vertical slices per half (<=1 means no slicing).
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
        print(f"Saved left/right halves for {base} -> {out_dir}")
        return

    slice_h = H // n_slices
    for i in range(n_slices):
        y0 = i * slice_h
        y1 = (i + 1) * slice_h if i < n_slices - 1 else H
        cv2.imwrite(os.path.join(out_dir, f"{base}_left_{i:02d}.png"),  left[y0:y1, :])
        cv2.imwrite(os.path.join(out_dir, f"{base}_right_{i:02d}.png"), right[y0:y1, :])

    print(f"Split {base} into {2 * n_slices} pieces -> {out_dir}")


def split_all_in_dir(crops_dir: str,
                     n_slices: int = 0,
                     out_dir: Optional[str] = None,
                     pattern: str = "cropped_torso_*.png") -> None:
    """
    Convenience helper (no private paths): process all matching images in a folder.

    - Skips files that end with '_color.png'.
    - Writes to `out_dir` if given; otherwise to '<crops_dir>/torso_slices'.

    Parameters
    ----------
    crops_dir : str
        Directory that contains cropped torso masks.
    n_slices : int
        Number of vertical slices per half.
    out_dir : Optional[str]
        Output directory. If None, uses '<crops_dir>/torso_slices'.
    pattern : str
        Glob pattern to match input files (default: 'cropped_torso_*.png').
    """
    if out_dir is None:
        out_dir = os.path.join(crops_dir, "torso_slices")

    if not os.path.isdir(crops_dir):
        raise NotADirectoryError(f"Directory not found: {crops_dir}")

    paths = sorted(glob(os.path.join(crops_dir, pattern)))
    total = 0
    for img_path in paths:
        if img_path.lower().endswith("_color.png"):
            continue
        try:
            split_cropped_torso(img_path, out_dir, n_slices=n_slices)
            total += 1
        except Exception as e:
            print(f"Error on {img_path}: {e}")

    print(f"Done: processed={total}, output_dir={out_dir}")
