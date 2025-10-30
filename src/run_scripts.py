# %%
import argparse
from pathlib import Path
import subprocess

from loguru import logger

parser = argparse.ArgumentParser()
# input .nii.gz file
parser.add_argument(
    "--input",
    type=Path,
    help="Path to the input NIfTI file.",
    default="../../data/example/Panoramix-cropped.nii.gz",
)
# output directory
parser.add_argument(
    "--output",
    type=Path,
    help="Path to the output directory.",
    default="/tmp/pci",
)
# temporary directory for nnUNet
parser.add_argument(
    "--tmpdir",
    type=Path,
    help="Path to temporary directory for nnUNet.",
    default="/tmp/nnUNet",
)
# skip existing outputs
parser.add_argument(
    "--skip_existing",
    action="store_true",
    help="Skip processing if output files already exist.",
)

args, _unknown = parser.parse_known_args()
# %%
args.output.mkdir(parents=True, exist_ok=True)
total_output = args.output / "total_segmentator.nii.gz"
total_output = total_output.resolve()
logger.info(
    f"Running Total Segmentator with input: {args.input} and output: {total_output}"
)

if args.skip_existing and total_output.exists():
    logger.warning(f"Total Segmentator output already exists at {total_output}, skipping.")
    # Skip running the command
else:
    # TotalSegmentator --task total -ml -bs -i INPUT -o OUTPUT
    # python -m totalsegmentator.bin.TotalSegmentator --task total -ml -bs -i INPUT -o OUTPUT
    command = [
        # "TotalSegmentator",
        "python",
    "-m",
    "totalsegmentator.bin.TotalSegmentator",
    "--task",
    "total",
    "-ml",
    "-bs",
    "-i",
    str(args.input),
    "-o",
    str(total_output),
]
    subprocess.check_call(command)
    logger.info("TotalSegmentator completed.")

#%%
# crop abdomen
logger.info("Cropping abdomen")
script = Path(__file__).parent / "crop_abdomen.py"
cropped_input = args.output / "abdomen_cropped.nii.gz"
cropped_total = args.output / "abdomen_cropped_total_segmentator.nii.gz"
command = [
    "python",
    str(script),
    "--input",
    str(args.input),
    "--total",
    str(total_output),
    "--output",
    str(cropped_input),
    "--output_total",
    str(cropped_total),
]
if args.skip_existing and cropped_input.exists() and cropped_total.exists():
    logger.warning(f"Cropped abdomen output already exists at {cropped_input} and {cropped_total}, skipping.")
else:
    subprocess.check_call(command)
    logger.info("Cropping abdomen completed.")

#%%
muscle_fat_output = args.output / "muscle_fat.nii.gz"
script = Path(__file__).parent / "../CT-Muscle-and-Fat-Segmentation/predict_muscle_fat.py"
script = script.resolve()
logger.info(f"Using script at: {script}")
# Run the muscle-fat segmentation script
command = [
    "python",
    str(script),
    "--input",
    str(cropped_input),
    "--output",
    str(muscle_fat_output),
]
if args.skip_existing and muscle_fat_output.exists():
    logger.warning(f"Muscle-Fat Segmentation output already exists at {muscle_fat_output}, skipping.")
else:
    logger.info(
        f"Running Muscle-Fat Segmentation with input: {cropped_input} and output: {muscle_fat_output}"
    )
    original_dir = Path.cwd()
    # Change working directory to the script's directory
    import os
    os.chdir(script.parent)
    # Set dummy nnUNet environment variables
    os.environ["nnUNet_raw"] = str(args.tmpdir / "raw")
    os.environ["nnUNet_preprocessed"] = str(args.tmpdir / "preprocessed")
    os.environ["nnUNet_results"] = str(args.tmpdir / "results")
    try:
        subprocess.check_output(command)
    except subprocess.CalledProcessError as e:
        logger.error(f"Muscle-Fat Segmentation failed with error: {e.output.decode()}")
        logger.error(f"Command: {' '.join(command)}")
        raise e
    # Change back to the original working directory
    os.chdir(original_dir)
    logger.info("Muscle-Fat Segmentation completed.")

#%%
logger.info("Segment PCI")
script = Path(__file__).parent / "segment_pci.py"
pci_output = args.output / "pci_segmentation.nii.gz"
command = [
    "python",
    str(script),
    "--total",
    str(cropped_total),
    "--muscle_fat",
    str(muscle_fat_output),
    "--output",
    str(pci_output),
]
if args.skip_existing and pci_output.exists():
    logger.warning(f"PCI Segmentation output already exists at {pci_output}, skipping.")
else:
    subprocess.check_call(command)
    logger.info("PCI Segmentation completed.")
# %%
logger.info("Visualize segmentations")
script = Path(__file__).parent / "visualize_segmentation.py"
image_output = args.output / "segmentation_visualization.png"
if args.skip_existing and image_output.exists():
    logger.warning(f"Visualization output already exists at {image_output}, skipping.")
else:
    command = [
        "python",
        str(script),
        "--image",
        str(cropped_input),
        "--total",
        str(cropped_total),
        "--muscle_fat",
        str(muscle_fat_output),
        "--pci",
        str(pci_output),
        "--output",
        str(image_output),
    ]
    subprocess.check_call(command)
    logger.info("Visualization completed.")