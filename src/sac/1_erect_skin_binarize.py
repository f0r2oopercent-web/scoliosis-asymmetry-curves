# erect_skin_binarize.py
# ------------------------------------------------------------
# Skin-region binarization core (publication-ready, no data paths)
#
# NOTE: This repository does not include images. Use the functions
# below within your own pipeline that supplies image paths.
# ------------------------------------------------------------

import os
import cv2
import numpy as np

# ===== Tunable parameters =====
CR_MIN, CR_MAX = 133, 173
CB_MIN, CB_MAX =  77, 127
KERNEL_SHAPE   = (3, 3)
CLOSE_ITERS    = 2
OPEN_ITERS     = 1
# ==============================

def skin_mask_only(img_bgr: np.ndarray) -> np.ndarray:
    """
    Convert BGR to YCrCb, binarize the skin region, and reduce noise via morphology.
    Returns a single-channel (uint8) mask with values in {0, 255}.
    """
    ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
    mask  = cv2.inRange(ycrcb, (0, CR_MIN, CB_MIN), (255, CR_MAX, CB_MAX))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, KERNEL_SHAPE)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=CLOSE_ITERS)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=OPEN_ITERS)
    return mask

def process_single_erect(img_path: str) -> bool:
    """
    Create and save a skin mask for a single image.
    The mask is saved next to the source image under a subfolder 'erect_masks_skin_only'
    with filename '<source>_mask.png'.
    """
    if not os.path.isfile(img_path):
        print(f"Warning: file not found: {img_path}")
        return False

    img = cv2.imread(img_path)
    if img is None:
        print(f"Warning: failed to load: {img_path}")
        return False

    mask = skin_mask_only(img)

    parent  = os.path.dirname(img_path)
    out_dir = os.path.join(parent, "erect_masks_skin_only")
    os.makedirs(out_dir, exist_ok=True)

    root, _  = os.path.splitext(os.path.basename(img_path))
    out_path = os.path.join(out_dir, f"{root}_mask.png")
    cv2.imwrite(out_path, mask)
    print(f"Saved: {out_path}")
    return True
