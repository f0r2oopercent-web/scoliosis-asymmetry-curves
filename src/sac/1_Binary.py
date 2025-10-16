# erect_skin_binarize.py
import os, glob
import cv2
import numpy as np

# ===== 튜닝 파라미터 =====
CR_MIN, CR_MAX = 133, 173
CB_MIN, CB_MAX =  77, 127
KERNEL_SHAPE   = (3, 3)
CLOSE_ITERS    = 2
OPEN_ITERS     = 1
# ========================

# ---- 경로/대상 설정(여기만 바꿔도 됨) ----
BASE_ROOT = r"C:\Users\f0r2o\PycharmProjects\XRAYSCO\8_8"
FIRST_PID = 24
LAST_PID  = 30
# ------------------------------------------

def skin_mask_only(img_b# erect_skin_binarize.py
import os, glob
import cv2
import numpy as np

# ===== 튜닝 파라미터 =====
CR_MIN, CR_MAX = 133, 173
CB_MIN, CB_MAX =  77, 127
KERNEL_SHAPE   = (3, 3)
CLOSE_ITERS    = 2
OPEN_ITERS     = 1
# ========================

# ---- 경로/대상 설정(여기만 바꿔도 됨) ----
BASE_ROOT = r"C:\Users\f0r2o\PycharmProjects\XRAYSCO\8_8"
FIRST_PID = 24
LAST_PID  = 30
# ------------------------------------------

def skin_mask_only(img_bgr: np.ndarray) -> np.ndarray:
    """BGR → YCrCb 후 피부 영역 이진화 + 모폴로지 노이즈 제거."""
    ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
    mask  = cv2.inRange(ycrcb, (0, CR_MIN, CB_MIN), (255, CR_MAX, CB_MAX))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, KERNEL_SHAPE)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=CLOSE_ITERS)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=OPEN_ITERS)
    return mask

def process_single_erect(jpg_path: str) -> bool:
    """단일 Erect 이미지에서 피부 마스크를 저장."""
    if not os.path.isfile(jpg_path):
        print(f"⚠️  파일 없음: {jpg_path}")
        return False
    img = cv2.imread(jpg_path)
    if img is None:
        print(f"⚠️  로드 실패: {jpg_path}")
        return False

    mask = skin_mask_only(img)

    parent  = os.path.dirname(jpg_path)
    out_dir = os.path.join(parent, "erect_masks_skin_only")
    os.makedirs(out_dir, exist_ok=True)

    root, _  = os.path.splitext(os.path.basename(jpg_path))
    out_path = os.path.join(out_dir, f"{root}_mask.png")
    cv2.imwrite(out_path, mask)
    print(f"✅ 저장: {out_path}")
    return True

def find_erect_image_for_pid(base_root: str, pid: int) -> str | None:
    """P{pid:03d}\\Erect\\P{pid:03d}_*_E_1.(jpg/jpeg/JPG/JPEG) 중 첫 번째를 반환."""
    pdir = os.path.join(base_root, f"P{pid:03d}", "Erect")
    patterns = [
        os.path.join(pdir, f"P{pid:03d}_*_E_1.jpg"),
        os.path.join(pdir, f"P{pid:03d}_*_E_1.jpeg"),
        os.path.join(pdir, f"P{pid:03d}_*_E_1.JPG"),
        os.path.join(pdir, f"P{pid:03d}_*_E_1.JPEG"),
    ]
    matches = []
    for pat in patterns:
        matches.extend(glob.glob(pat))
    matches = sorted(matches)
    if not matches:
        print(f"❌ 대상 없음: {os.path.join(pdir, f'P{pid:03d}_*_E_1.jpg')}")
        return None
    if len(matches) > 1:
        print(f"ℹ️ P{pid:03d}: {len(matches)}개 발견 → 첫 번째 사용: {os.path.basename(matches[0])}")
    return matches[0]

def process_range(base_root: str, first: int, last: int):
    total, ok = 0, 0
    for pid in range(first, last + 1):
        path = find_erect_image_for_pid(base_root, pid)
        if path:
            total += 1
            ok += process_single_erect(path)
    print(f"\n✔ 완료: 대상 {total}개, 저장 {ok}개")

if __name__ == "__main__":
    process_range(BASE_ROOT, FIRST_PID, LAST_PID)
gr: np.ndarray) -> np.ndarray:
    """BGR → YCrCb 후 피부 영역 이진화 + 모폴로지 노이즈 제거."""
    ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
    mask  = cv2.inRange(ycrcb, (0, CR_MIN, CB_MIN), (255, CR_MAX, CB_MAX))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, KERNEL_SHAPE)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=CLOSE_ITERS)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=OPEN_ITERS)
    return mask

def process_single_erect(jpg_path: str) -> bool:
    """단일 Erect 이미지에서 피부 마스크를 저장."""
    if not os.path.isfile(jpg_path):
        print(f"⚠️  파일 없음: {jpg_path}")
        return False
    img = cv2.imread(jpg_path)
    if img is None:
        print(f"⚠️  로드 실패: {jpg_path}")
        return False

    mask = skin_mask_only(img)

    parent  = os.path.dirname(jpg_path)
    out_dir = os.path.join(parent, "erect_masks_skin_only")
    os.makedirs(out_dir, exist_ok=True)

    root, _  = os.path.splitext(os.path.basename(jpg_path))
    out_path = os.path.join(out_dir, f"{root}_mask.png")
    cv2.imwrite(out_path, mask)
    print(f"✅ 저장: {out_path}")
    return True

def find_erect_image_for_pid(base_root: str, pid: int) -> str | None:
    """P{pid:03d}\\Erect\\P{pid:03d}_*_E_1.(jpg/jpeg/JPG/JPEG) 중 첫 번째를 반환."""
    pdir = os.path.join(base_root, f"P{pid:03d}", "Erect")
    patterns = [
        os.path.join(pdir, f"P{pid:03d}_*_E_1.jpg"),
        os.path.join(pdir, f"P{pid:03d}_*_E_1.jpeg"),
        os.path.join(pdir, f"P{pid:03d}_*_E_1.JPG"),
        os.path.join(pdir, f"P{pid:03d}_*_E_1.JPEG"),
    ]
    matches = []
    for pat in patterns:
        matches.extend(glob.glob(pat))
    matches = sorted(matches)
    if not matches:
        print(f"❌ 대상 없음: {os.path.join(pdir, f'P{pid:03d}_*_E_1.jpg')}")
        return None
    if len(matches) > 1:
        print(f"ℹ️ P{pid:03d}: {len(matches)}개 발견 → 첫 번째 사용: {os.path.basename(matches[0])}")
    return matches[0]

def process_range(base_root: str, first: int, last: int):
    total, ok = 0, 0
    for pid in range(first, last + 1):
        path = find_erect_image_for_pid(base_root, pid)
        if path:
            total += 1
            ok += process_single_erect(path)
    print(f"\n✔ 완료: 대상 {total}개, 저장 {ok}개")

if __name__ == "__main__":
    process_range(BASE_ROOT, FIRST_PID, LAST_PID)
