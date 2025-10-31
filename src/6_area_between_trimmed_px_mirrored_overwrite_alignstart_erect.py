# area_between_trimmed_px_mirrored_overwrite_alignstart_erect.py
# ------------------------------------------------------------
# Paper-ready plotting of area between trimmed left/right edge profiles.
# - No private dataset paths, no PID loops, no __main__.
# - English-only comments/prints; Matplotlib "Agg" backend.
# - Right is mirrored; optional start alignment; integrates |Δx| over y.
# - Saves high-res figures; CSV/JSON saving optional.
# ------------------------------------------------------------

import os
import glob
import json
import re
from typing import Tuple, Optional

import numpy as np
import pandas as pd
import cv2

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
from matplotlib.ticker import AutoMinorLocator, MaxNLocator

# ================== Options (tweak as needed) ==================
# Relative subfolders under an Erect directory:
EDGES_DIR      = os.path.join("erect_crops", "edges")
SLICES_DIR     = os.path.join("erect_crops", "torso_slices")
TRIMMED_ROOT   = os.path.join("erect_crops", "trimmed_results")

ALIGN_START     = True            # Align the starting x (y-min) between left and mirrored-right
OUTPUT_TO_R1    = True            # If True, save figures under '<in_dir>/R1'
FIGSIZE_MM      = (180, 120)      # Figure size in millimeters (paper readability)
PRESERVE_ASPECT = True            # Keep 1 px : 1 px scale in the plot
LINE_W          = 2.2
ALPHA_FILL      = 0.22

# Figure-only mode:
GRAPH_ONLY          = True        # If True, do not save CSV/JSON; figures only
USE_FULL_WIDTH_XPX  = True        # Y-axis (x[px]) span uses full tile width
USE_ROI_HEIGHT_YPX  = True        # X-axis (y[px]) span uses ROI-only (union of y)
PAD_FRAC_Y_RANGE    = 0.03        # Padding fraction for y-axis (x dir)
PAD_FRAC_X_RANGE    = 0.02        # Padding fraction for x-axis (y dir)
MAJOR_TICKS_TARGET  = 6           # Target number of major ticks
# ===============================================================


# --------- Matplotlib (paper) style ----------
def _setup_matplotlib_for_paper():
    serif_candidates = [
        "Times New Roman", "Times", "CMU Serif", "Noto Serif CJK KR", "DejaVu Serif"
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    chosen = next((c for c in serif_candidates if c in available), "DejaVu Serif")
    mpl.rcParams.update({
        "font.family": chosen,
        "mathtext.fontset": "stix",
        "axes.unicode_minus": False,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.labelsize": 10, "axes.titlesize": 11,
        "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
        "axes.linewidth": 0.9, "savefig.dpi": 600,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
        "patch.linewidth": 0.0,
    })

def _mm(mm: float) -> float:
    return mm / 25.4

def _paper_fig(figsize_mm) -> Tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(_mm(figsize_mm[0]), _mm(figsize_mm[1])), constrained_layout=True)
    return fig, ax

def _save_pub(fig: plt.Figure, base_noext: str) -> None:
    fig.savefig(base_noext + ".png", dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(base_noext + ".pdf",              bbox_inches="tight", facecolor="white")
    fig.savefig(base_noext + ".svg",              bbox_inches="tight", facecolor="white")

_setup_matplotlib_for_paper()


# --------- Path helpers ----------
def _core_root_from_left_stem(stem: str) -> str:
    """Strip typical '_left[_trim*]' suffixes to get a core name."""
    s = re.sub(r"(_left|-left)([-_]?trim(med)?)?$", "", stem, flags=re.IGNORECASE)
    s = re.sub(r"([-_]?trim(med)?)$", "", s, flags=re.IGNORECASE)
    return s

def _find_right_trim_csv(in_dir: str, left_trim_csv: str) -> Optional[str]:
    """Find the matching right-trimmed CSV for a given left-trimmed CSV."""
    stem = os.path.splitext(os.path.basename(left_trim_csv))[0]
    core = _core_root_from_left_stem(stem)
    cand = os.path.join(in_dir, f"{core}_right_trimmed.csv")
    if os.path.isfile(cand):
        return cand
    for pat in [f"{core}_right*trim*.csv", f"{core}*right*trim*.csv"]:
        hits = sorted(glob.glob(os.path.join(in_dir, pat)))
        if hits:
            return hits[0]
    return None

def _get_tile_hw(erect_dir: str, core: str) -> Tuple[Optional[int], Optional[int]]:
    """Return (H, W) from an available PNG (right tile or edge vis)."""
    p = os.path.join(erect_dir, SLICES_DIR, f"{core}_right.png")
    if os.path.isfile(p):
        img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            h, w = img.shape[:2]
            return h, w
    p2 = os.path.join(erect_dir, EDGES_DIR, f"{core}_right_vis.png")
    if os.path.isfile(p2):
        img = cv2.imread(p2, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            h, w = img.shape[:2]
            return h, w
    return None, None

def _ensure_out_dir(base_dir: str) -> str:
    if OUTPUT_TO_R1:
        out = os.path.join(base_dir, "R1")
        os.makedirs(out, exist_ok=True)
        return out
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def _remove_old_outputs(out_dir: str, core: str) -> None:
    pref = os.path.join(out_dir, f"{core}_area_between")
    for p in glob.glob(pref + ".*"):
        try:
            os.remove(p)
        except Exception:
            pass


# --------- Layout helper for right-side boxes ----------
def _place_boxes_right(fig: plt.Figure, ax: plt.Axes, legend, stat_text: str) -> None:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    leg_box_fig = legend.get_window_extent(renderer=renderer).transformed(fig.transFigure.inverted())
    gap = 0.012
    x_right = leg_box_fig.x1
    y_top   = leg_box_fig.y0 - gap
    fig.text(x_right, y_top, stat_text,
             ha="right", va="top",
             bbox=dict(boxstyle="round,pad=0.28",
                       facecolor="white", alpha=0.98,
                       edgecolor="#cfcfcf", linewidth=0.7))


# --------- Core processing for one pair ----------
def _area_from_pair(erect_dir: str, in_dir: str,
                    left_trim_csv: str, right_trim_csv: str, core: str) -> bool:
    dfL = pd.read_csv(left_trim_csv).sort_values("y")
    dfR = pd.read_csv(right_trim_csv).sort_values("y")
    if dfL.empty or dfR.empty:
        return False

    # 1) Mirror right about tile width
    H, W = _get_tile_hw(erect_dir, core)
    if W is None or H is None:
        print(f"Skip (unknown width/height): {core}")
        return False
    xR_m = (W - 1) - dfR["x_sub"].to_numpy()

    # 2) Unify y and interpolate
    yL = dfL["y"].to_numpy(dtype=float)
    yR = dfR["y"].to_numpy(dtype=float)
    y_u = np.union1d(yL, yR)
    xL_u = np.interp(y_u, yL, dfL["x_sub"].to_numpy())
    xR_u = np.interp(y_u, yR, xR_m)

    # 3) Optional start alignment
    if ALIGN_START and len(y_u) > 0:
        y0  = y_u.min()
        xL0 = float(np.interp(y0, y_u, xL_u))
        xR0 = float(np.interp(y0, y_u, xR_u))
        xR_u = xR_u + (xL0 - xR0)

    # 4) Integrate |Δx|
    abs_dx = np.abs(xL_u - xR_u)
    A_px2  = np.trapz(abs_dx, y_u)
    H_roi  = float(y_u.max() - y_u.min()) if len(y_u) > 1 else 0.0
    mean_abs_dx_px = (A_px2 / H_roi) if H_roi > 0 else float("nan")

    # 5) Output directory and (optional) data saving
    out_dir  = _ensure_out_dir(in_dir)
    _remove_old_outputs(out_dir, core)
    out_pref = os.path.join(out_dir, f"{core}_area_between")

    if not GRAPH_ONLY:
        pd.DataFrame({
            "y": y_u,
            "x_left": xL_u,
            "x_right_mirrored_aligned" if ALIGN_START else "x_right_mirrored": xR_u,
            "abs_dx": abs_dx
        }).to_csv(out_pref + ".csv", index=False)

        with open(out_pref + "_summary.json", "w", encoding="utf-8") as f:
            json.dump({
                "A_between_px2": float(A_px2),
                "height_px": H_roi,
                "mean_abs_dx_px": None if np.isnan(mean_abs_dx_px) else float(mean_abs_dx_px),
                "width_used_px": int(W),
                "align_start": ALIGN_START
            }, f, ensure_ascii=False, indent=2)

    # 6) Figure (1:1 pixel scale option; nice ticks/grid for papers)
    c_left  = "#1f77b4"
    c_right = "#ff7f0e"
    c_fill  = "#cae9f5"

    fig, ax = _paper_fig(figsize_mm=FIGSIZE_MM)
    ax.fill_between(y_u, xL_u, xR_u, alpha=ALPHA_FILL, color=c_fill, linewidth=0, zorder=1, label="|Δx| area")
    ax.plot(y_u, xL_u,  color=c_left,  linewidth=LINE_W, zorder=3, label="Left (trimmed)")
    ax.plot(y_u, xR_u,  color=c_right, linewidth=LINE_W, linestyle=(0, (6, 3)), zorder=3,
            label=("Right mirrored (aligned)" if ALIGN_START else "Right mirrored"))

    ax.set_xlabel("y (px)")      # vertical position
    ax.set_ylabel("x (px)")      # horizontal position (waist line)

    # Axis ranges (preserve physical sense)
    # X-axis (y): ROI-only + padding (or full height if USE_ROI_HEIGHT_YPX=False)
    if USE_ROI_HEIGHT_YPX:
        x_min = float(y_u.min())
        x_max = float(y_u.max())
    else:
        x_min = 0.0
        x_max = float(H - 1)
    x_pad = PAD_FRAC_Y_RANGE * max(1.0, (x_max - x_min)) if x_max > x_min else 2.0
    ax.set_xlim(x_min - x_pad, x_max + x_pad)

    # Y-axis (x): full tile width by default
    if USE_FULL_WIDTH_XPX:
        y_min = -PAD_FRAC_X_RANGE * (W - 1)
        y_max = (W - 1) * (1.0 + PAD_FRAC_X_RANGE)
    else:
        y_min = float(min(xL_u.min(), xR_u.min()))
        y_max = float(max(xL_u.max(), xR_u.max()))
        y_pad = PAD_FRAC_X_RANGE * max(1.0, (y_max - y_min))
        y_min -= y_pad
        y_max += y_pad
    ax.set_ylim(y_min, y_max)

    # 1 px : 1 px aspect (optional)
    if PRESERVE_ASPECT:
        ax.set_aspect("equal", adjustable="box")
    else:
        ax.set_aspect("auto")

    # Ticks/grid (paper-friendly)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.xaxis.set_major_locator(MaxNLocator(nbins=MAJOR_TICKS_TARGET))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=MAJOR_TICKS_TARGET))
    ax.grid(True, which="major", linewidth=0.6, alpha=0.28)
    ax.grid(True, which="minor", linewidth=0.4, alpha=0.18)
    ax.tick_params(which="both", direction="out", length=3.0, width=0.9)
    ax.tick_params(which="minor", length=2.0, width=0.7)

    legend = ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0),
                       borderaxespad=0.0, frameon=True, fancybox=True,
                       handlelength=2.8, handletextpad=0.8)
    legend.get_frame().set_facecolor("white")
    legend.get_frame().set_edgecolor("#d0d0d0")
    legend.get_frame().set_linewidth(0.8)

    stat = (
        f"A = {A_px2:.2f} px²\n"
        f"H(ROI) = {H_roi:.2f} px\n"
        f"mean|Δx| = {mean_abs_dx_px:.3f} px\n"
        f"W(tile) = {W}"
    )
    _place_boxes_right(fig, ax, legend, stat)

    _save_pub(fig, out_pref + "_fill")
    plt.close(fig)
    return True


# --------- Public APIs (no private paths, no __main__) ----------
def process_trimmed_subdir(erect_dir: str, in_dir: str) -> None:
    """
    Process a single trimmed-results directory under an Erect dir.
    Looks for '*_left_trimmed.csv' (skips already-trimmed-right variations without a pair).
    Saves figures into 'in_dir' or 'in_dir/R1' (if OUTPUT_TO_R1=True).
    """
    lefts = sorted(glob.glob(os.path.join(in_dir, "*_left_trimmed.csv")))
    if not lefts:
        print(f"Skip: no '*_left_trimmed.csv' in -> {in_dir}")
        return

    any_done = False
    for lcsv in lefts:
        core = _core_root_from_left_stem(os.path.splitext(os.path.basename(lcsv))[0])
        rcsv = _find_right_trim_csv(in_dir, lcsv)
        if not rcsv:
            print(f"Pair not found for left-trimmed: {os.path.basename(lcsv)} in {in_dir}")
            continue
        try:
            ok = _area_from_pair(erect_dir, in_dir, lcsv, rcsv, core)
            any_done |= ok
            if ok:
                out_dir = os.path.join(in_dir, "R1") if OUTPUT_TO_R1 else in_dir
                print(f"Processed: {core} -> figures in {out_dir}")
        except Exception as e:
            print(f"Error on {os.path.basename(lcsv)}: {e}")

    if not any_done:
        print(f"No pairs processed in: {in_dir}")

def process_erect_dir(erect_dir: str) -> None:
    """
    Process one Erect directory. Scans:
      '<erect_dir>/erect_crops/trimmed_results/*' (subfolders),
    or uses the trimmed root itself if it directly contains trimmed CSVs.
    """
    trimmed_root = os.path.join(erect_dir, TRIMMED_ROOT)
    if not os.path.isdir(trimmed_root):
        print(f"Skip: trimmed_results not found -> {trimmed_root}")
        return

    sub_dirs = [p for p in glob.glob(os.path.join(trimmed_root, "*")) if os.path.isdir(p)] or [trimmed_root]
    any_dir = False
    for in_dir in sub_dirs:
        process_trimmed_subdir(erect_dir, in_dir)
        any_dir = True

    if not any_dir:
        print(f"No trimmed subdirectories in: {trimmed_root}")
