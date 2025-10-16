# compare_real_vs_zero_diff_onepair.py
# ------------------------------------------------------------
# Compare real vs. zero-diff–adjusted left/right edge profiles
# for a single pair. No hardcoded dataset paths or __main__.
# ------------------------------------------------------------

import os
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # safe for headless
import matplotlib.pyplot as plt
import cv2


def _to_left_csv(path: str) -> Optional[str]:
    """If `path` is CSV, return it; if it's an image, return sibling '<stem>.csv' if present."""
    root, ext = os.path.splitext(path)
    if ext.lower() == ".csv":
        return path
    cand = root + ".csv"
    return cand if os.path.isfile(cand) else None


def _find_erect_dir_from(path: str) -> Optional[str]:
    """Walk up to locate an 'Erect' directory containing this path."""
    d = os.path.dirname(path)
    while True:
        if os.path.basename(d).lower() == "erect":
            return d
        nd = os.path.dirname(d)
        if nd == d:
            return None
        d = nd


def _get_core_from_left(left_csv: str) -> str:
    """Derive the <core> stem from a '*_left*.csv' filename."""
    name = os.path.splitext(os.path.basename(left_csv))[0]
    for suf in ("_left_trimmed", "_left-trimmed", "_left_trim", "_left"):
        if name.endswith(suf):
            return name[:-len(suf)]
    return name


def _get_width(erect_dir: str, core: str,
               dfL: Optional[pd.DataFrame] = None,
               dfR: Optional[pd.DataFrame] = None) -> Optional[int]:
    """
    Prefer width from PNG tiles, fall back to max(x_sub) from CSVs.
    Looks for:
      <Erect>/erect_crops/torso_slices/<core>_right.png
      <Erect>/erect_crops/edges/<core>_right_vis.png
    """
    p = os.path.join(erect_dir, "erect_crops", "torso_slices", f"{core}_right.png")
    if os.path.isfile(p):
        im = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        if im is not None:
            return int(im.shape[1])

    p2 = os.path.join(erect_dir, "erect_crops", "edges", f"{core}_right_vis.png")
    if os.path.isfile(p2):
        im = cv2.imread(p2, cv2.IMREAD_GRAYSCALE)
        if im is not None:
            return int(im.shape[1])

    if dfL is not None and dfR is not None and (not dfL.empty) and (not dfR.empty):
        return int(np.ceil(max(dfL["x_sub"].max(), dfR["x_sub"].max())) + 1)

    return None


def compare_real_vs_zero_diff(
    left_path: str,
    right_csv_path: str,
    output_dir: Optional[str] = None,
    figure_dpi: int = 300,
) -> Optional[str]:
    """
    Create a two-panel figure (real vs. zero-diff–adjusted) for a single pair.

    Parameters
    ----------
    left_path : str
        Path to left profile (CSV) or an image whose sibling CSV exists.
    right_csv_path : str
        Path to right-trimmed CSV.
    output_dir : Optional[str]
        Where to save the figure. Defaults to the directory of `right_csv_path`.
    figure_dpi : int
        DPI for the saved PNG.

    Returns
    -------
    Optional[str]
        Output PNG path if successful, otherwise None.
    """
    left_csv = _to_left_csv(left_path)
    if not left_csv or not os.path.isfile(left_csv):
        print("Skip: left CSV not found ->", (os.path.splitext(left_path)[0] + ".csv"))
        return None
    if not os.path.isfile(right_csv_path):
        print("Skip: right CSV not found ->", right_csv_path)
        return None

    dfL = pd.read_csv(left_csv).sort_values("y")
    dfR = pd.read_csv(right_csv_path).sort_values("y")
    if dfL.empty or dfR.empty:
        print("Skip: one or both CSVs are empty.")
        return None

    erect_dir = _find_erect_dir_from(left_csv)
    if not erect_dir:
        print("Skip: could not locate an 'Erect' parent directory from:", left_csv)
        return None

    core = _get_core_from_left(left_csv)
    W = _get_width(erect_dir, core, dfL, dfR)
    if not W:
        print("Skip: could not determine tile width (W).")
        return None

    # Mirror right across tile width
    dfR_m = dfR.copy()
    dfR_m["x_sub"] = (W - 1) - dfR_m["x_sub"]

    # Merge on common y
    df = dfL.merge(dfR_m, on="y", suffixes=("_L", "_R"))
    if df.empty:
        print("Skip: no common y between left and right.")
        return None

    # Compute zero-diff adjustment
    df["diff"] = df["x_sub_R"] - df["x_sub_L"]
    mask = df["diff"] > 0
    df["x_L_adj"] = df["x_sub_L"]
    df["x_R_adj"] = df["x_sub_R"]
    df.loc[mask,  "x_R_adj"] = df.loc[mask, "x_sub_L"]
    df.loc[~mask, "x_L_adj"] = df.loc[~mask, "x_sub_R"]

    # Real-view coordinates
    df["x_real_L"] = df["x_sub_L"]
    df["x_real_R"] = (W - 1) - df["x_sub_R"]
    df["x_adj_real_L"] = df["x_L_adj"]
    df["x_adj_real_R"] = (W - 1) - df["x_R_adj"]

    df = df.sort_values("y")
    ymin, ymax = float(df["y"].min()), float(df["y"].max())

    # Plot (two panels)
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(1, 2, figsize=(10, 6), sharey=True)

    axes[0].plot(df["x_real_L"], df["y"], label="Left",  lw=1.5)
    axes[0].plot(df["x_real_R"], df["y"], label="Right", lw=1.5)
    axes[0].set_ylim(ymin, ymax)
    axes[0].invert_yaxis()
    axes[0].set_title("A. Real (pre-adjust)")
    axes[0].set_xlabel("x (px)")
    axes[0].set_ylabel("y (row)")
    axes[0].legend()

    axes[1].plot(df["x_adj_real_L"], df["y"], label="Left adj",  lw=1.5)
    axes[1].plot(df["x_adj_real_R"], df["y"], label="Right adj", lw=1.5)
    axes[1].set_ylim(ymin, ymax)
    axes[1].invert_yaxis()
    axes[1].set_title("B. Zero-diff (real view)")
    axes[1].set_xlabel("x (px)")
    axes[1].legend()

    fig.suptitle(core, y=0.98)
    fig.tight_layout()

    out_dir = output_dir or os.path.dirname(right_csv_path)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"real_vs_zero_diff_fixed_{core}.png")
    plt.savefig(out_path, dpi=figure_dpi)
    plt.close()
    print("Saved:", out_path)
    return out_path
