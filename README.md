# Scoliosis Asymmetry Curves 
Dohee Lee¹, Junghun Kim²* and Sang-il Choi³*
¹School of Computer Software, Daegu Catholic University, Gyeongsan-si, Republic of Korea  
²School of Computer Software, Daegu Catholic University, Gyeongsan-si, Republic of Korea  
³School of Computer Software, Daegu Catholic University, Gyeongsan-si, Republic of Korea

*Correspondence: fainal2@cu.ac.kr ; sangilchoi@cu.ac.kr

This repository contains the implementation modules of a marker-less scoliosis asymmetry pipeline derived from our work.  
**No datasets, demo images, or runnable entry points are included.** The code is organized as importable modules so you can run the pipeline with your own data.

The data used in this study were collected after obtaining approval from the Institutional Review Board (IRB) of Kyungpook National University Hospital, in accordance with ethical guidelines (IRB number: KNUH 2025).

## Scope
- Source code only (see `src/` and top-level modules listed below).
- No example data, no notebooks, no CLI/`__main__` scripts.
- All paths are **caller-provided**; modules do not hard-code private directories.

## Modules (high level, this repository)
- `erect_skin_binarize.py` — skin-region binarization in YCrCb with morphology cleanup.
- `src/step_manual_crop.py` — interactive/manual ROI cropping utilities (array in/out; no disk I/O).
- `split_erect_cropped_torso.py` — split cropped torso masks into left/right (and optional vertical slices).
- `detect_and_plot_edges_erect.py` — sub-pixel edge extraction per row; left vs. mirrored-right symmetry plots.
- `trim_only_erect_final_grouped.py` — trim paired left/right edge profiles to a **common y-range** and save visualizations.
- `area_between_trimmed_px_mirrored_overwrite_alignstart_erect.py` — mirror right, (optionally) align starts, integrate **|Δx|**, and save paper-ready figures.
- `compare_real_vs_zero_diff_onepair.py` — two-panel comparison (**real view** vs. **zero-diff adjusted**) for a single pair.


## Data & Privacy
- Original images are not publicly available due to privacy restrictions.
- This repository intentionally does **not** include any data or executable entry points.

## Citation / Contact
If you use or review this code, please cite the manuscript.  
Correspondence: **Dohee Lee**, School of Computer Software, Daegu Catholic University.
