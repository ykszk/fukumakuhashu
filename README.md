# Peritoneal Cancer Radiomics

Segment abdominal CT scans and compute radiomics features over visceral fat (VAT),
split into upper/middle/lower Peritoneal Cancer Index (PCI) regions.

## Pipeline (`src/run_scripts.py`)

Given a NIfTI CT volume, each run produces, in order:

1. **TotalSegmentator** (`total` task) — organs, bone, vessels, muscle (~117 structures)
2. **Abdomen crop** — crops to liver-top through sacrum-bottom (+ margin), using the `total` segmentation as a landmark reference
3. **TotalSegmentator** (`tissue_4_types` task) — subcutaneous fat / visceral fat (VAT) / skeletal muscle / intermuscular fat
4. **PCI segmentation** — takes the VAT class, clears out non-fat contamination using a `remove` mask built from the `total` labels (solid organs/bone/vessels excluded outright; digestive-tract organs eroded by a small margin first, so perivisceral fat right next to bowel isn't also stripped), then splits the result into lower/middle/upper PCI zones using anatomical landmarks (sacrum, iliac crest, costal arch, liver dome)
5. **Visualization** — axial/coronal/sagittal panels (CT, TotalSegmentator, tissue mask, PCI), cropped to the body
6. **Pyradiomics** feature extraction over the three PCI zones

Each stage's output is cached under `--output`; pass `--skip_existing` to skip stages whose output files are already present (useful when only re-running later stages, e.g. after a `segment_pci.py` change).

## Setup

```bash
uv sync
```

pyradiomics is pinned to an upstream git commit (see `[tool.uv.sources]` in `pyproject.toml`) and has C extensions. On Windows with Python 3.13 it installs from a wheel prebuilt from that commit (`vendor/`), so no C compiler (MSVC) is needed; elsewhere it's built from source, which needs one. Rebuild the wheel whenever the pin changes; the steps are in the `pyproject.toml` comment.

Requires a **TotalSegmentator academic/commercial license** for the `tissue_4_types` task (the `total` task is free). Register one with:

```bash
uv run totalseg_set_license -l <your-license-key>
```

Get a free academic key at https://backend.totalsegmentator.com/license-academic/.

## Usage

Input must be a NIfTI (`.nii.gz`) CT volume. DICOM series can be converted with `dicom2nifti` (already a transitive dependency via TotalSegmentator) or `to-niigz.bat` on Windows.

```bash
uv run python src/run_scripts.py --input <path/to/ct.nii.gz> --output <output_dir> --skip_existing
```

Outputs land in `<output_dir>/`: `total_segmentator.nii.gz`, `abdomen_cropped.nii.gz`, `tissue_4_types.nii.gz`, `remove.nii.gz`, `pci_segmentation.nii.gz`, `segmentation_visualization.png`, `pyradiomics_features.csv` (one row per PCI zone).

The shape features `Elongation`, `Flatness` and the `Major`/`Minor`/`LeastAxisLength` come out of pyradiomics as complex numbers with a zero imaginary part (e.g. `(0.97+0j)`): it takes their square roots from `np.linalg.eigvals`, which returns complex values under numpy 2. `run_scripts.py` rewrites those cells as plain real numbers after extraction, so the CSV loads as numeric; cells with a nonzero imaginary part are left as written.

## Ascites segmentation (optional, separate)

`ascites/` is a standalone environment for the [Task505_TCGA-OV ascites model](https://github.com/rsummers11/Ascites) (nnU-Net v1) — kept separate from the main pipeline since it needs a different Python version (3.10) and doesn't share any dependencies with it. See `ascites/README.md` for setup. It isn't wired into `run_scripts.py`; run it separately on a case's `abdomen_cropped.nii.gz`.

## Notes

- `to-niigz.bat` / `run_segmentation.bat` are drag-and-drop wrappers for Windows: drop a DICOM folder on the first (→ `C:\hashu\dcm2niix\<folder name>[_<series>].nii.gz`, one file per series, via `src/convert_dicom.py`; the user then moves the series to analyze into `C:\hashu\input`), a `.nii.gz` file on the second (→ `C:\hashu\output\<case name>\`). `run_ascites.bat` takes the same `.nii.gz` (or the case's output folder) after the main run and writes `ascites.nii.gz` there; it needs the model extracted to `C:\hashu\code\models\ascites_model`, which `setup_ascites_model.bat` does (double-click it with the archive saved at `C:\hashu\downloads\ascites_model.tar.gz`, or drop the archive on it; it also installs the ascites environment). They expect the repo cloned at `C:\hashu\code`; set `HASHU_DIR` to use another workspace. Paths must be ASCII: SimpleITK can't open non-ASCII paths on Windows, so both refuse them up front.
- `docs/user-manual.md` is the end-user manual (Japanese, for the drag-and-drop workflow). Build its PDF with `uv run docs/build_manual_pdf.py` (needs Microsoft Edge or Chrome); the PDF is not committed.
- CPU-only inference: TotalSegmentator's `total` task takes ~10 min/case, `tissue_4_types` ~1-2 min/case, pyradiomics extraction varies widely (~2-50 min) with how much VAT a case has.
