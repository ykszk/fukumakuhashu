# Convert a DICOM folder to NIfTI for to-niigz.bat (drag-and-drop).
# Output goes to a staging folder (dcm2niix); the user then moves the one series
# to analyze into the input folder. A folder with one series gives
# <output_dir>/<folder name>.nii.gz; several series give one file each, named
# <folder name>_<series number>_<description>.nii.gz.
#
# Series are grouped and converted here rather than with
# dicom2nifti.convert_directory, which names files only by series number and
# description (so two series sharing them overwrite each other) and only logs
# series that fail to convert.
import argparse
import os
import re
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import dicom2nifti.common as common
import dicom2nifti.convert_dicom as convert_dicom
import dicom2nifti.settings
from dicom2nifti.convert_dir import _is_valid_imaging_dicom
from pydicom import dcmread

parser = argparse.ArgumentParser()
parser.add_argument("dicom_dir", type=Path, help="Folder containing DICOM files.")
parser.add_argument("output_dir", type=Path, help="Folder to write .nii.gz files to.")
args = parser.parse_args()

dicom_dir = args.dicom_dir.resolve()
name = dicom_dir.name
# SimpleITK (used by the pipeline) can't open non-ASCII paths on Windows, so the
# case name, which becomes the .nii.gz and output folder names, must be ASCII.
if not name.isascii():
    print(f"エラー: フォルダー名「{name}」に全角文字が含まれています。")
    print("フォルダー名を半角英数字（例: 001）に変更してから、もう一度ドラッグ＆ドロップしてください。")
    sys.exit(1)
args.output_dir.mkdir(parents=True, exist_ok=True)


def series_label(ds):
    """ASCII-only label from series number and description (or a fallback)."""
    parts = [str(ds.get("SeriesNumber", "") or "")]
    for tag in ("SeriesDescription", "SequenceName", "ProtocolName"):
        if ds.get(tag):
            parts.append(str(ds.get(tag)))
            break
    label = re.sub(r"[^A-Za-z0-9-]+", "_", "_".join(parts)).strip("_")
    return label or "series"


print(f"変換中: {dicom_dir}")
series = defaultdict(list)
for root, _, files in os.walk(dicom_dir):
    for f in files:
        path = os.path.join(root, f)
        try:
            if not common.is_dicom_file(path):
                continue
            ds = dcmread(path, defer_size="1 KB", stop_before_pixels=False, force=dicom2nifti.settings.pydicom_read_force)
        except Exception:
            continue
        if _is_valid_imaging_dicom(ds):
            series[ds.SeriesInstanceUID].append(ds)

if not series:
    print("エラー: このフォルダーに変換できるDICOM画像が見つかりませんでした。")
    sys.exit(1)

# Destination names, unique even when series share number and description.
if len(series) == 1:
    names = {uid: f"{name}.nii.gz" for uid in series}
else:
    names, used = {}, set()
    for uid, slices in series.items():
        base, n = f"{name}_{series_label(slices[0])}", 1
        while (candidate := base + (f"_{n}" if n > 1 else "") + ".nii.gz") in used:
            n += 1
        used.add(candidate)
        names[uid] = candidate

existing = [args.output_dir / n for n in names.values() if (args.output_dir / n).exists()]
if existing:
    for dst in existing:
        print(f"エラー: 同じ名前のファイルがすでにあります: {dst}")
    print("上書きしないよう中止しました。不要なら削除してから、もう一度実行してください。")
    sys.exit(1)

created, failed = [], []
with tempfile.TemporaryDirectory() as tmp:
    for uid, slices in series.items():
        tmp_file = Path(tmp) / names[uid]
        try:
            convert_dicom.dicom_array_to_nifti(slices, str(tmp_file), True)
        except Exception as e:
            failed.append((names[uid], e))
            continue
        dst = args.output_dir / names[uid]
        shutil.move(str(tmp_file), str(dst))
        created.append(dst)

for n, e in failed:
    print(f"警告: シリーズを変換できませんでした（{n}）: {e}")
if not created:
    print("エラー: 変換できたシリーズがありませんでした。")
    sys.exit(1)

if len(created) == 1:
    print(f"完了: {created[0]}")
else:
    print(f"このフォルダーには {len(created)} 個のシリーズがありました。次のファイルを作成しました:")
    for dst in created:
        print(f"  {dst}  ({dst.stat().st_size / 1e6:.1f} MB)")
