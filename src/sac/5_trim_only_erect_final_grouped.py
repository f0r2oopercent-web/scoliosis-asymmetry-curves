# trim_only_erect_final_grouped.py
# ------------------------------------------------------------
# Trim paired *_left.csv / *_right.csv to their common y-range
# and save trimmed CSVs + visualizations under:
#   <Erect>/erect_crops/trimmed_results/<core>/
# - No private dataset paths
# - No __main__ entrypoint
# - English-only comments/prints; no emojis
# ------------------------------------------------------------

import os
import glob
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _read_profile_csv(p: str) -> pd.DataFrame:
    """Robust CSV reader accepting headers like (y, x_sub) or (x, y), etc."""
    try:
        df = pd.read_csv(p)
    except Exception:
        df = pd.read_csv(p, header=None)

    cols = [c.lower() if isinstance(c, str) else c for c in df.columns]

    if "y" in cols:
        y = df[df.columns[cols.index("y")]].to_numpy()
    else:
        y = df.iloc[:, 0].to_numpy()

    if "x_sub" in cols:
        x = df[df.columns[cols.index("x_sub")]].to_numpy()
    elif "x" in cols:
        x = df[df.columns[cols.index("x")]].to_numpy()
    else:
        x = df.iloc[:, 1].to_numpy()

    idx = np.argsort(y)
    return pd.DataFrame({"y": y[idx].astype(float), "x_sub": x[idx].astype(float)})


def _core_from_left(left_csv_path: str) -> str:
    """Derive a core stem from a '*_left*.csv' file name."""
    stem = os.path.splitext(os.path.basename(left_csv_path))[0]
    for suf in ("_left_trimmed", "_left-trimmed", "_left_trim", "_left"):
        if stem.endswith(suf):
            return stem[: -len(suf)]
    return stem


def _save_single_vis(df: pd.DataFrame, start_y: float, end_y: float, out_png: str, title: str) -> None:
    """Save a single-curve visualization with start/end y markers."""
    y = df["y"].to_numpy()
    x = df["x_sub"].to_numpy()
    plt.figure(figsize=(6, 8))
    plt.plot(x, y, "-o", ms=2.5, lw=1.2)
    plt.axhline(start_y, ls="--", lw=1)
    plt.axhline(end_y,   ls="--", lw=1)
    plt.gca().invert_yaxis()
    plt.title(title)
    plt.xlabel("x_sub")
    plt.ylabel("y")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()


def _save_overlay(dfL: pd.DataFrame, dfR: pd.DataFrame, start_y: float, end_y: float, out_png: str, title: str) -> None:
    """Save an overlay visualization of left/right curves with common y markers."""
    plt.figure(figsize=(6, 8))
    plt.plot(dfL["x_sub"], dfL["y"], "-o", ms=2.5, lw=1.2, label="Left")
    plt.plot(dfR["x_sub"], dfR["y"], "-o", ms=2.5, lw=1.2, label="Right")
    plt.axhline(start_y, ls="--", lw=1, label="start_y")
    plt.axhline(end_y,   ls="--", lw=1, label="end_y")
    plt.gca().invert_yaxis()
    plt.title(title)
    plt.xlabel("x_sub")
    plt.ylabel("y")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()


def process_erect_dir(erect_dir: str) -> None:
    """
    Process one Erect directory:
      - Reads paired CSVs from '<erect_dir>/erect_crops/edges'
      - Finds the common y-range for each left/right pair
      - Writes trimmed CSVs and visualizations under:
        '<erect_dir>/erect_crops/trimmed_results/<core>/'
    """
    edges_dir = os.path.join(erect_dir, "erect_crops", "edges")
    if not os.path.isdir(edges_dir):
        print(f"Skip: edges directory not found -> {edges_dir}")
        return

    left_list = sorted(
        p for p in glob.glob(os.path.join(edges_dir, "*_left*.csv"))
        if "trim" not in os.path.basename(p).lower()
    )
    if not left_list:
        print(f"Skip: no '*_left*.csv' in -> {edges_dir}")
        return

    any_done = False
    for left_csv in left_list:
        core = _core_from_left(left_csv)
        right_csv = os.path.join(edges_dir, f"{core}_right.csv")
        if not os.path.isfile(right_csv):
            cands = [
                p for p in glob.glob(os.path.join(edges_dir, f"{core}_right*.csv"))
                if "trim" not in os.path.basename(p).lower()
            ]
            if not cands:
                print(f"Pair not found for: {os.path.basename(left_csv)}")
                continue
            right_csv = sorted(cands)[0]

        dfL = _read_profile_csv(left_csv).sort_values("y")
        dfR = _read_profile_csv(right_csv).sort_values("y")
        if dfL.empty or dfR.empty:
            print(f"Empty CSV pair: {core}")
            continue

        start_y = max(dfL["y"].min(), dfR["y"].min())
        end_y   = min(dfL["y"].max(), dfR["y"].max())
        if end_y <= start_y:
            print(f"No overlapping y-range: {core}")
            continue

        L_trim = dfL[(dfL["y"] >= start_y) & (dfL["y"] <= end_y)].copy()
        R_trim = dfR[(dfR["y"] >= start_y) & (dfR["y"] <= end_y)].copy()

        out_dir = os.path.join(erect_dir, "erect_crops", "trimmed_results", core)
        os.makedirs(out_dir, exist_ok=True)

        left_trim_csv  = os.path.join(out_dir, f"{core}_left_trimmed.csv")
        right_trim_csv = os.path.join(out_dir, f"{core}_right_trimmed.csv")
        left_vis_png   = os.path.join(out_dir, f"{core}_left_trimmed.png")
        right_vis_png  = os.path.join(out_dir, f"{core}_right_trimmed.png")
        overlay_png    = os.path.join(out_dir, f"{core}_trimmed_overlay_both.png")

        L_trim.to_csv(left_trim_csv, index=False)
        R_trim.to_csv(right_trim_csv, index=False)

        _save_single_vis(L_trim, start_y, end_y, left_vis_png,  f"{core} - LEFT (trimmed)")
        _save_single_vis(R_trim, start_y, end_y, right_vis_png, f"{core} - RIGHT (trimmed)")
        _save_overlay(L_trim, R_trim, start_y, end_y, overlay_png, f"{core} - overlay (trimmed)")

        print(f"Trimmed: {core} -> {out_dir}")
        any_done = True

    if any_done:
        print(f"Done: {erect_dir}")
    else:
        print(f"No pairs processed in: {erect_dir}")
