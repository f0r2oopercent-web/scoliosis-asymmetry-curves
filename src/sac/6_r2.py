# compare_real_vs_zero_diff_onepair.py
# 입력: 왼쪽(좌) 파일 경로(*.csv 또는 *.png), 오른쪽(우) CSV 경로
# 동작: torso_slices의 *_right.png 폭으로 오른쪽 미러 → 공통 y에서 zero-diff 보정
# 출력: 두 패널 이미지(real 전/후) 한 장 저장 (오른쪽 CSV가 있는 폴더에 저장)

import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import cv2

# ====== 여기를 사용자 파일 경로로 채움 ======
LEFT_PATH  = r"C:\Users\f0r2o\PycharmProjects\XRAYSCO\8_8\P024\Erect\erect_crops\trimmed_results\cropped_torso_P024_46.9T6-T11_39.4T11-L4_E_1\cropped_torso_P024_46.9T6-T11_39.4T11-L4_E_1_left_trimmed.csv"
RIGHT_CSV  = r"C:\Users\f0r2o\PycharmProjects\XRAYSCO\8_8\P024\Erect\erect_crops\trimmed_results\cropped_torso_P024_46.9T6-T11_39.4T11-L4_E_1\cropped_torso_P024_46.9T6-T11_39.4T11-L4_E_1_right_trimmed.csv"
# ===========================================

# ====== Times New Roman 전역 글꼴 설정 ======
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["axes.unicode_minus"] = False
# ===========================================

def _to_left_csv(path):
    root, ext = os.path.splitext(path)
    if ext.lower() == ".csv":
        return path
    cand = root + ".csv"
    return cand if os.path.isfile(cand) else None

def _find_erect_dir_from(path):
    d = os.path.dirname(path)
    while True:
        if os.path.basename(d).lower() == "erect":
            return d
        nd = os.path.dirname(d)
        if nd == d:
            return None
        d = nd

def _get_core_from_left(left_csv):
    name = os.path.splitext(os.path.basename(left_csv))[0]
    for suf in ("_left_trimmed", "_left-trimmed", "_left_trim", "_left"):
        if name.endswith(suf):
            return name[:-len(suf)]
    return name

def _get_width(erect_dir, core, dfL=None, dfR=None):
    p = os.path.join(erect_dir, "erect_crops", "torso_slices", f"{core}_right.png")
    if os.path.isfile(p):
        im = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        if im is not None:
            return im.shape[1]
    p2 = os.path.join(erect_dir, "erect_crops", "edges", f"{core}_right_vis.png")
    if os.path.isfile(p2):
        im = cv2.imread(p2, cv2.IMREAD_GRAYSCALE)
        if im is not None:
            return im.shape[1]
    if dfL is not None and dfR is not None:
        return int(np.ceil(max(dfL["x_sub"].max(), dfR["x_sub"].max())) + 1)
    return None

def main():
    left_csv = _to_left_csv(LEFT_PATH)
    if not left_csv or not os.path.isfile(left_csv):
        print("❌ 왼쪽 CSV가 필요합니다:", os.path.splitext(LEFT_PATH)[0] + ".csv")
        sys.exit(1)
    if not os.path.isfile(RIGHT_CSV):
        print("❌ 오른쪽 CSV가 없습니다:", RIGHT_CSV); sys.exit(1)

    dfL = pd.read_csv(left_csv).sort_values("y")
    dfR = pd.read_csv(RIGHT_CSV).sort_values("y")
    if dfL.empty or dfR.empty:
        print("❌ CSV가 비어 있습니다."); sys.exit(1)

    erect_dir = _find_erect_dir_from(left_csv)
    if not erect_dir:
        print("❌ 'Erect' 상위 폴더를 찾지 못했습니다."); sys.exit(1)

    core = _get_core_from_left(left_csv)
    W = _get_width(erect_dir, core, dfL, dfR)
    if not W:
        print("❌ 타일 폭(W)을 결정할 수 없습니다."); sys.exit(1)

    # 오른쪽 미러
    dfR_m = dfR.copy()
    dfR_m["x_sub"] = (W - 1) - dfR_m["x_sub"]

    # 공통 y만 병합
    df = dfL.merge(dfR_m, on="y", suffixes=("_L", "_R"))
    if df.empty:
        print("❌ 공통 y가 없습니다."); sys.exit(1)

    # diff 및 zero-diff 보정
    df["diff"] = df["x_sub_R"] - df["x_sub_L"]
    mask = df["diff"] > 0
    df["x_L_adj"] = df["x_sub_L"]
    df["x_R_adj"] = df["x_sub_R"]
    df.loc[mask,  "x_R_adj"] = df.loc[mask, "x_sub_L"]
    df.loc[~mask, "x_L_adj"] = df.loc[~mask, "x_sub_R"]

    # real view 좌표
    df["x_real_L"] = df["x_sub_L"]
    df["x_real_R"] = (W - 1) - df["x_sub_R"]
    df["x_adj_real_L"] = df["x_L_adj"]
    df["x_adj_real_R"] = (W - 1) - df["x_R_adj"]

    df = df.sort_values("y")
    ymin, ymax = df["y"].min(), df["y"].max()

    # 플롯
    fig, axes = plt.subplots(1, 2, figsize=(10, 6), sharey=True)

    axes[0].plot(df["x_real_L"], df["y"], label="Left",  lw=1.5)
    axes[0].plot(df["x_real_R"], df["y"], label="Right", lw=1.5)
    axes[0].set_ylim(ymin, ymax); axes[0].invert_yaxis()
    axes[0].set_title("A. Real (pre-adjust)")
    axes[0].set_xlabel("x (px)"); axes[0].set_ylabel("y (row)")
    axes[0].legend()

    axes[1].plot(df["x_adj_real_L"], df["y"], label="Left adj",  lw=1.5)
    axes[1].plot(df["x_adj_real_R"], df["y"], label="Right adj", lw=1.5)
    axes[1].set_ylim(ymin, ymax); axes[1].invert_yaxis()
    axes[1].set_title("B. Zero-diff (real view)")
    axes[1].set_xlabel("x (px)")
    axes[1].legend()

    fig.suptitle(core, y=0.98)
    fig.tight_layout()

    out_dir  = os.path.dirname(RIGHT_CSV)
    out_path = os.path.join(out_dir, f"real_vs_zero_diff_fixed_{core}.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("✅ 저장:", out_path)

if __name__ == "__main__":
    main()
