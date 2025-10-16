# src/step_manual_crop.py
# ------------------------------------------------------------
# Code-only utilities for manual cropping.
# - No filesystem I/O (all inputs/outputs are numpy arrays).
# - No __main__ entrypoint.
# - Optional interactive ROI selection via OpenCV GUI.
# ------------------------------------------------------------

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict

import numpy as np
import cv2


@dataclass
class CropUIConfig:
    """Viewer/overlay configuration for manual cropping (caller-provided if needed)."""
    max_w: int = 1400            # max display width
    max_h: int = 900             # max display height
    overlay_alpha: float = 0.35
    window_title: str = (
        "Erect Cropper — [E] new ROI  [Y] reuse previous  [O] toggle view  [S] skip  [Q/ESC] quit"
    )


def make_overlay(color_bgr: np.ndarray, mask_gray: np.ndarray, alpha: float = 0.35) -> np.ndarray:
    """Return BGR preview with red overlay where mask > 0."""
    img = color_bgr.copy()
    red = np.zeros_like(img)
    red[..., 2] = 255
    m = mask_gray > 0
    overlay = img.copy()
    overlay[m] = red[m]
    return cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)


def resize_for_display(img: np.ndarray, max_w: int, max_h: int) -> Tuple[np.ndarray, float]:
    """Return (resized image for preview, scale). Downscale only; no upscaling."""
    h, w = img.shape[:2]
    s = min(max_w / w, max_h / h, 1.0)
    if s < 1.0:
        img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return img, s


def draw_text_multiline(img: np.ndarray, lines: List[str]) -> None:
    """Draw multi-line caption (outline + white) at the top-left corner; preview use only."""
    y = 24
    for ln in lines:
        cv2.putText(img, ln, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 3, cv2.LINE_AA)
        cv2.putText(img, ln, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        y += 22


def crop_with_padding(mask: np.ndarray, color: Optional[np.ndarray],
                      roi_xywh: Tuple[int, int, int, int],
                      pad_px: int = 0) -> Dict[str, np.ndarray]:
    """
    Crop mask/color arrays by ROI with optional padding. No disk I/O.

    Parameters
    ----------
    mask : np.ndarray            # HxW (uint8 recommended)
    color: Optional[np.ndarray]  # HxWx3 BGR or None
    roi_xywh: (x, y, w, h)       # coordinates in original resolution
    pad_px : int

    Returns
    -------
    dict with keys:
      - 'mask' : np.ndarray (cropped mask)
      - 'color': np.ndarray (cropped color)  # only if color is not None
    """
    H, W = mask.shape[:2]
    x, y, w, h = map(int, roi_xywh)
    x0 = max(0, x - pad_px)
    y0 = max(0, y - pad_px)
    x1 = min(W, x + w + pad_px)
    y1 = min(H, y + h + pad_px)

    out = {"mask": mask[y0:y1, x0:x1].copy()}
    if color is not None:
        out["color"] = color[y0:y1, x0:x1].copy()
    return out


def interactive_select_and_crop(color_bgr: np.ndarray,
                                mask_gray: np.ndarray,
                                last_roi_xywh: Optional[Tuple[int, int, int, int]] = None,
                                ui: Optional[CropUIConfig] = None,
                                pad_px: int = 0,
                                return_preview_mode: bool = False) -> Dict[str, object]:
    """
    Optional OpenCV GUI utility to select an ROI and perform cropping.
    - No paths or file saving here; the caller decides.
    - Returns selected ROI and cropped arrays.

    Returns
    -------
    dict with:
      - 'roi': (x, y, w, h) or None     # None when skipped/quit
      - 'crops': {'mask':..., 'color':... (optional)}
      - 'preview_mode': int (0=overlay, 1=mask→BGR, 2=color) if return_preview_mode=True
    """
    if ui is None:
        ui = CropUIConfig()

    overlay = make_overlay(color_bgr, mask_gray, ui.overlay_alpha)
    previews = [overlay, cv2.cvtColor(mask_gray, cv2.COLOR_GRAY2BGR), color_bgr]
    mode = 0

    cv2.namedWindow(ui.window_title, cv2.WINDOW_NORMAL)
    try:
        while True:
            view = previews[mode].copy()
            disp, s = resize_for_display(view, ui.max_w, ui.max_h)

            msg = [
                "[E] new ROI  [Y] reuse previous  [O] toggle view  [S] skip  [Q/ESC] quit",
                "selectROI: ENTER/SPACE to accept, C to cancel",
            ]
            if last_roi_xywh is not None:
                x, y, w, h = last_roi_xywh
                rx, ry, rw, rh = int(x * s), int(y * s), int(w * s), int(h * s)
                cv2.rectangle(disp, (rx, ry), (rx + rw, ry + rh), (0, 255, 0), 2)
                msg.append(f"Prev ROI: x={x}, y={y}, w={w}, h={h} (press Y to reuse)")

            draw_text_multiline(disp, msg)
            cv2.imshow(ui.window_title, disp)
            k = cv2.waitKey(0) & 0xFF

            if k in (ord('o'), ord('O')):
                mode = (mode + 1) % 3
                continue

            if k in (ord('s'), ord('S')):  # skip
                return {"roi": None, "crops": {}, **({"preview_mode": mode} if return_preview_mode else {})}

            if k in (ord('q'), ord('Q'), 27):  # ESC
                return {"roi": None, "crops": {}, **({"preview_mode": mode} if return_preview_mode else {})}

            if k in (ord('y'), ord('Y')) and (last_roi_xywh is not None):
                crops = crop_with_padding(mask_gray, color_bgr, last_roi_xywh, pad_px=pad_px)
                out = {"roi": last_roi_xywh, "crops": crops}
                if return_preview_mode:
                    out["preview_mode"] = mode
                return out

            if k in (ord('e'), ord('E')) or (last_roi_xywh is None):
                roi_disp = cv2.selectROI(ui.window_title, disp, showCrosshair=True, fromCenter=False)
                if roi_disp[2] <= 0 or roi_disp[3] <= 0:
                    continue
                # Restore to original scale
                x = int(roi_disp[0] / s)
                y = int(roi_disp[1] / s)
                w = int(roi_disp[2] / s)
                h = int(roi_disp[3] / s)
                roi_xywh = (x, y, w, h)

                crops = crop_with_padding(mask_gray, color_bgr, roi_xywh, pad_px=pad_px)
                out = {"roi": roi_xywh, "crops": crops}
                if return_preview_mode:
                    out["preview_mode"] = mode
                return out

    finally:
        cv2.destroyAllWindows()  # ensure window teardown even on exceptions

