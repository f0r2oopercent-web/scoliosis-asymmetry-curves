# API_EN

This document summarizes the **public API** of the modules we prepared: function signatures, inputs/outputs, side effects (I/O), and error behavior. No datasets are shipped; callers must provide paths explicitly.

---

## Common Environment

* Python ≥ 3.9
* Dependencies: `numpy`, `opencv-python` (`cv2`), `pandas`, `matplotlib` (Agg backend), `dataclasses`, `typing`
* Directory layout assumed for edge/trimmed artifacts:

  ```
  <Erect>/
    erect_crops/
      torso_slices/         # *_left.png, *_right.png
      edges/                # *_left.csv, *_right.csv, *_right_vis.png
      trimmed_results/
        <core>/
          *_left_trimmed.csv
          *_right_trimmed.csv
  ```
* All outputs are written only where the caller has write permission.

---

## 1) `erect_skin_binarize.py`

Skin-region binarization core.

### Functions

**`skin_mask_only(img_bgr: np.ndarray) -> np.ndarray`**

* Converts BGR to YCrCb, thresholds by `(CR_MIN..CR_MAX, CB_MIN..CB_MAX)`, then morphology Close → Open.
* Input: `img_bgr` (`H×W×3`, `uint8`, BGR).
* Returns: binary mask (`H×W`, `uint8`, values {0, 255}).
* Side effects: none.
* Errors: none (input validity is the caller’s responsibility).

**`process_single_erect(img_path: str) -> bool`**

* Creates and saves a skin mask as `<parent>/erect_masks_skin_only/<stem>_mask.png`.
* Input: readable image path.
* Returns: success flag.
* Side effects: writes PNG, creates output directory if needed.
* Errors: on missing/unreadable image, prints a warning and returns `False`.

---

## 2) `src/step_manual_crop.py`

Manual cropping utilities (no filesystem I/O).

### Dataclass

**`CropUIConfig`**

* `max_w: int = 1400`, `max_h: int = 900` — preview bounds (downscale only)
* `overlay_alpha: float = 0.35` — overlay opacity
* `window_title: str` — OpenCV window title (includes key hints)

### Functions

**`make_overlay(color_bgr: np.ndarray, mask_gray: np.ndarray, alpha: float = 0.35) -> np.ndarray`**

* Produces a BGR preview with red overlay where `mask > 0`.
* Side effects: none.

**`resize_for_display(img: np.ndarray, max_w: int, max_h: int) -> tuple[np.ndarray, float]`**

* Returns a downscaled preview and the scale factor; no upscaling.

**`draw_text_multiline(img: np.ndarray, lines: list[str]) -> None`**

* Draws outlined white text at the top-left for preview.
* Side effects: modifies `img` in place.

**`crop_with_padding(mask: np.ndarray, color: Optional[np.ndarray], roi_xywh: tuple[int,int,int,int], pad_px: int = 0) -> dict[str, np.ndarray]`**

* Crops arrays by ROI in original coordinates with optional padding.
* Returns: `{"mask": cropped_mask, "color": cropped_color}` (color only when provided).
* Side effects: none.

**`interactive_select_and_crop(color_bgr: np.ndarray, mask_gray: np.ndarray, last_roi_xywh: Optional[tuple[int,int,int,int]] = None, ui: Optional[CropUIConfig] = None, pad_px: int = 0, return_preview_mode: bool = False) -> dict[str, object]`**

* GUI ROI tool; returns selected ROI and crops.
* Returns keys:

  * `'roi'`: `(x, y, w, h)` or `None`
  * `'crops'`: `{'mask':..., 'color':... (optional)}`
  * `'preview_mode'` (optional): `0=overlay, 1=mask→BGR, 2=color`
* Keys: `E` new ROI, `Y` reuse previous, `O` toggle view, `S` skip, `Q/ESC` quit.
* Side effects: creates/destroys a window.

---

## 3) `split_erect_cropped_torso.py`

Split a grayscale torso mask into left/right halves or vertical slices.

### Functions

**`split_cropped_torso(img_path: str, out_dir: str, n_slices: int = 0) -> None`**

* If `n_slices <= 1`: saves two images (`*_left.png`, `*_right.png`).
* If `n_slices > 1`: splits each half into `n_slices` horizontal bands and saves.
* Side effects: creates output directory and writes PNGs.
* Errors: `FileNotFoundError` when input cannot be loaded.

**`split_all_in_dir(crops_dir: str, n_slices: int = 0, out_dir: Optional[str] = None, pattern: str = "cropped_torso_*.png") -> None`**

* Processes all matching images; skips files ending with `_color.png`.
* Output directory defaults to `<crops_dir>/torso_slices` if not provided.
* Side effects: writes PNGs, logs progress.
* Errors: raises `NotADirectoryError` if `crops_dir` is missing.

---

## 4) `detect_and_plot_edges_erect.py`

Subpixel edge detection per row and symmetric (left vs mirrored-right) plotting.

### Functions

**`detect_subpixel_edge_row(row: np.ndarray, threshold: int) -> Optional[float]`**

* Returns the first rising-edge crossing `threshold` via linear interpolation (`v0 < T <= v1`), or `None`.

**`process_tile(tile_path: str, out_dir: str, threshold: int, is_right: bool) -> tuple[str, int]`**

* For right tiles, horizontally flips first; computes subpixel edge `x` for each row.
* Saves `<base>.csv` with `y,x_sub` and `<base>_vis.png` with overlaid points.
* Returns: `(base_name, tile_width)`.
* Side effects: writes CSV and PNG.

**`plot_symmetry(out_dir: str, left_name: str, right_name: str, tile_width: int) -> None`**

* Mirrors right by `tile_width - 1` and plots both curves to `<left>_<right>_symmetry.png`.
* Side effects: writes PNG.

**`process_erect_dir(erect_dir: str, threshold: int = 128) -> None`**

* Pairs `*_left.png` with `*_right.png` in `<Erect>/erect_crops/torso_slices`, writes CSV/vis under `<Erect>/erect_crops/edges`.
* Side effects: writes CSVs/PNGs, prints logs.

---

## 5) `trim_only_erect_final_grouped.py`

Trim paired left/right edge profiles to their **common y-range** and save results/visualizations.

### Public Function

**`process_erect_dir(erect_dir: str) -> None`**

* Reads pairs from `<Erect>/erect_crops/edges`.
* Computes overlapping `y` interval `[start_y, end_y]`, trims both profiles, saves under `<Erect>/erect_crops/trimmed_results/<core>/`:

  * `*_left_trimmed.csv`, `*_right_trimmed.csv`
  * single-curve PNGs and an overlay PNG
* Side effects: writes files, prints logs.

### Internal Utilities

* `_read_profile_csv(p) -> pd.DataFrame` — tolerant CSV reader for `(y,x_sub)` or `(x,y)` columns.
* `_core_from_left(left_csv_path) -> str` — derive `core` name from `*_left*.csv`.
* `_save_single_vis(...)`, `_save_overlay(...)` — save figures.

---

## 6) `area_between_trimmed_px_mirrored_overwrite_alignstart_erect.py`

Mirror the right trimmed profile, optionally align starting `x`, integrate **|Δx|** over `y`, and save paper-ready figures.

### Key Options (module-level)

* `ALIGN_START: bool` — align right (mirrored) curve to left at `y = min(y)` via constant offset.
* `OUTPUT_TO_R1: bool` — save into `<in_dir>/R1` instead of `<in_dir>`.
* `FIGSIZE_MM: tuple[int, int]` — figure size in millimeters.
* `PRESERVE_ASPECT: bool` — enforce 1 px : 1 px aspect.
* `GRAPH_ONLY: bool` — if `True`, only figures are saved; CSV/JSON are skipped.
* Axis/tick styling: `USE_FULL_WIDTH_XPX`, `USE_ROI_HEIGHT_YPX`, `PAD_FRAC_Y_RANGE`, `PAD_FRAC_X_RANGE`, `MAJOR_TICKS_TARGET`.

### Public Functions

**`process_trimmed_subdir(erect_dir: str, in_dir: str) -> None`**

* Expects `*_left_trimmed.csv` and matching `*_right_trimmed.csv` in `in_dir`.
* Mirrors right by tile width; unifies `y` with interpolation; optional start alignment; integrates `|Δx|`.
* Saves figures as `<core>_area_between_fill.(png|pdf|svg)` under `in_dir` or `in_dir/R1`.
* If `GRAPH_ONLY=False`, also writes `<core>_area_between.csv` and `<core>_area_between_summary.json`.
* Side effects: writes/overwrites files, may delete prior outputs with the same prefix, prints logs.

**`process_erect_dir(erect_dir: str) -> None`**

* Runs `process_trimmed_subdir` over all subdirectories of `<Erect>/erect_crops/trimmed_results/`, or the root if it contains trimmed CSVs directly.
* Side effects: writes figures (and optionally data), prints logs.

---

## 7) `compare_real_vs_zero_diff_onepair.py`

Two-panel comparison for a single pair: **real view** vs. **zero-diff adjusted**.

### Public Function

**`compare_real_vs_zero_diff(left_path: str, right_csv_path: str, output_dir: Optional[str] = None, figure_dpi: int = 300) -> Optional[str]`**

* Inputs:

  * `left_path`: path to `*_left_trimmed.csv` or an image with a sibling CSV of the same stem.
  * `right_csv_path`: path to `*_right_trimmed.csv`.
  * `output_dir`: optional; default is the directory of `right_csv_path`.
* Behavior:

  1. Locates the `<Erect>` parent and infers tile width `W` from `torso_slices/<core>_right.png` or `edges/<core>_right_vis.png` (falls back to CSV maxima).
  2. Mirrors right: `x_R ← (W - 1) - x_R`.
  3. Merges on common `y` and applies zero-diff adjustment at each `y`.
  4. Converts back to real-view `x` for both panels and saves `real_vs_zero_diff_fixed_<core>.png`.
* Returns: output PNG path on success; `None` on failure.
* Side effects: writes a PNG in `output_dir` (creates the folder if needed), prints concise logs.

---

## Error Handling Principles

* Missing files / load failures: print concise English messages and skip gracefully (return `False`/`None` as appropriate).
* Empty CSVs / no common `y` / unknown tile width: skip the problematic pair.
* Visualization/save issues: print a short message; do not raise unless explicitly documented.

---

## Recommended Pipeline (module interplay)

1. `erect_skin_binarize.process_single_erect` (optional preprocessing)
2. Manual cropping externally or via `step_manual_crop.interactive_select_and_crop`
3. `split_erect_cropped_torso.split_all_in_dir` (left/right and optional vertical slices)
4. `detect_and_plot_edges_erect.process_erect_dir` (subpixel edges to CSV + visualizations)
5. `trim_only_erect_final_grouped.process_erect_dir` (trim to common `y` and plot)
6. `area_between_trimmed_px_mirrored_overwrite_alignstart_erect.process_erect_dir` (|Δx| area and paper figures)
7. `compare_real_vs_zero_diff_onepair.compare_real_vs_zero_diff` (pair-wise real vs. adjusted comparison)

---

## License / Data Privacy

* No images are included in the repository. Callers must provide local paths.
* Ensure no personally identifiable information is written to artifacts.

