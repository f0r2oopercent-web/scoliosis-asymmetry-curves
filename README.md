# Scoliosis Asymmetry Curves — Code-only Repository

This repository provides the **implementation modules** of a markerless scoliosis
asymmetry pipeline. **No datasets or runnable entry points are included.**
Validation/statistics are described in the manuscript; additional materials are
available **upon reasonable request**.

## Scope
- Source code only (`src/sac/*`).  
- No sample images, no execution scripts, no notebooks.

## Modules (high level)
- `binary.py`   — image binarization
- `crop.py`     — ROI/waist-region cropping
- `split.py`    — left/right split
- `edge.py`     — contour extraction
- `trim.py`     — background removal & refinement
- `reflect.py`  — reflection & alignment (r1/r2)
- `metrics.py`  — Δx(y), total area A, mean |Δx|

> Detailed API contracts are documented in `docs/API.md`.

## Data & Privacy
- Original images are not publicly available due to privacy restrictions.
- This repository intentionally does **not** include any data or executable entry points.

## Citation / Contact
If you use or review this code, please cite the manuscript.  
Correspondence: **Dohee Lee**, School of Computer Software, Daegu Catholic University.
