# %%
import argparse
from loguru import logger
from pathlib import Path

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

args, _unknown = parser.parse_known_args()
# %%
args.output.mkdir(parents=True, exist_ok=True)
total_output = args.output / "total_segmentator.nii.gz"
logger.info(
    f"Running Total Segmentator with input: {args.input} and output: {total_output}"
)
import subprocess

# TotalSegmentator --task total -ml -bs -i INPUT -o OUTPUT
command = [
    "TotalSegmentator",
    "--task",
    "total",
    "-ml",
    "-bs",
    "-i",
    str(args.input),
    "-o",
    str(total_output),
]
subprocess.run(command)
logger.info("TotalSegmentator completed.")

#%%
muscle_fat_output = args.output / "muscle_fat.nii.gz"
logger.info(
    f"Running Muscle-Fat Segmentation with input: {args.input} and output: {muscle_fat_output}"
)
script = Path(__file__).parent / "../CT-Muscle-and-Fat-Segmentation/predict_muscle_fat.py"
original_dir = Path.cwd()
# Change working directory to the script's directory
import os
os.chdir(script.parent)
# Set dummy nnUNet environment variables
os.environ["nnUNet_raw"] = str(args.tmpdir / "raw")
os.environ["nnUNet_preprocessed"] = str(args.tmpdir / "preprocessed")
os.environ["nnUNet_results"] = str(args.tmpdir / "results")
# Run the muscle-fat segmentation script
command = [
    "python3",
    str(script),
    "--input",
    str(args.input),
    "--output",
    str(muscle_fat_output),
]
subprocess.run(command)
# Change back to the original working directory
os.chdir(original_dir)
logger.info("Muscle-Fat Segmentation completed.")

#%%
logger.info("Segment PCI")
script = Path(__file__).parent / "segment_pci.py"
command = [
    "python3",
    str(script),
    "--total",
    str(total_output),
    "--muscle_fat",
    str(muscle_fat_output),
    "--output",
    str(args.output / "pci_segmentation.nii.gz"),
]
subprocess.run(command)
logger.info("PCI Segmentation completed.")
# %%
logger.info("Visualize segmentations")
script = Path(__file__).parent / "visualize_segmentation.py"
command = [
    "python3",
    str(script),
    "--input",
    str(args.input),
    "--total",
    str(total_output),
    "--muscle_fat",
    str(muscle_fat_output),
    "--pci",
    str(args.output / "pci_segmentation.nii.gz"),
    "--output",
    str(args.output / "segmentation_visualization.png"),
]
subprocess.run(command)
logger.info("Visualization completed.")