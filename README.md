# Scoliosis Asymmetry Curves

**Dohee Lee¹, Junghun Kim²*, Sang-il Choi³***
¹–³ School of Computer Software, Daegu Catholic University, Gyeongsan-si, Republic of Korea
*Corresponding authors: [fainal2@cu.ac.kr](mailto:fainal2@cu.ac.kr), [sangilchoi@cu.ac.kr](mailto:sangilchoi@cu.ac.kr)

This repository provides the implementation code for a **marker-less lumbar asymmetry analysis pipeline**, which extracts left/right waist contours from posterior torso images and, via mirrored alignment and common y-range harmonization, derives asymmetry curves and related metrics. The code is organized as step-wise modules; all paths are explicitly provided by the caller. The repository does **not** include real subject photographs; only a small, de-identified **X-ray–derived avatar** sample is provided to verify pipeline structure.

The collection and use of real human data were conducted in accordance with ethical guidelines **after approval** from the Institutional Review Board (IRB) of **Kyungpook National University Hospital** (Approval No.: **KNUH 2025**).


## 1. Scope and Purpose

The aims of this repository are: (i) to provide **readable, reusable, and modular source code** enabling researchers to apply the pipeline to their own datasets, and (ii) to transparently illustrate pipeline connectivity and output formats using an **avatar-based sample** within the bounds of public sharing. Command-line entry points and a `__main__` executable are **not** provided; example execution should be performed within the caller’s environment.


## 2. Module Composition (High-Level)

The core modules are as follows.
First, `erect_skin_binarize.py` performs skin-region binarization in the YCrCb color space with morphological cleanup, providing a robust basis for contour extraction.
Second, `step_manual_crop.py` offers manual (interactive) ROI specification, adhering to array I/O to avoid unnecessary disk access.
Third, `split_erect_cropped_torso.py` splits a cropped torso mask into left and right halves (optionally with vertical slicing).
Fourth, `detect_and_plot_edges_erect.py` extracts sub-pixel left contours and mirrored right contours for each image row (y) and prepares basic symmetry visualization materials.
Fifth, `trim_only_erect_final_grouped.py` harmonizes the valid segments of left/right profiles to a **common y-range**, preserving homology for subsequent integration and comparisons.
Sixth, `area_between_trimmed_px_mirrored_overwrite_alignstart_erect.py` mirrors the right profile, optionally aligns starting positions, and integrates the absolute difference (|Δx(y)|) to produce summary metrics and publication-ready figures.
Seventh, `compare_real_vs_zero_diff_onepair.py` provides a two-panel comparison for a single pair, contrasting the **real view** and the **zero-difference–adjusted** view.


## 3. Data Composition and Privacy

No real human photographs are distributed in this repository. A small, de-identified set of **X-ray–derived avatar images** is included solely to reproduce pipeline connectivity and output format.
Additional data may be provided **upon reasonable request** to the corresponding authors, subject to IRB approval conditions and institutional policies.


## 4. Usage Assumptions and Reproducibility

The code takes caller-provided paths as inputs and is implemented to avoid dependence on any specific operating environment. Preprocessing stages are configured to behave **deterministically** where feasible. Morphological kernels, interpolation methods, and visualization parameters (e.g., resolution and fonts) are set consistently with journal publication standards. When introducing stochastic components, users should explicitly specify random seeds.


## 5. Data Availability

The real human data used in the study are IRB-approved and are **not** intended for public distribution. This repository includes only a **subset of de-identified avatar samples**. Additional data may be shared **upon reasonable request** through the corresponding authors, in compliance with the IRB approval scope and institutional guidelines.
