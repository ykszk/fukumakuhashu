import argparse
import os

parser = argparse.ArgumentParser(description="Run the Task505_TCGA-OV ascites nnU-Net v1 model.")
parser.add_argument("--input", required=True, help="Path to a NIfTI file (will be used as the sole modality).")
parser.add_argument("--output", required=True, help="Path to write the output segmentation NIfTI.")
parser.add_argument(
    "--model_dir",
    default=os.path.join(os.path.dirname(__file__), "..", "models", "ascites_model"),
    help="Path to the extracted ascites_model.tar.gz contents.",
)
args = parser.parse_args()

from nnunet.inference import predict

model_path = os.path.join(
    args.model_dir,
    "nnUNet_trained_models/nnUNet/3d_fullres/Task505_TCGA-OV/nnUNetTrainerV2__nnUNetPlansv2.1",
)

predict.predict_cases(
    model=model_path,
    list_of_lists=[[args.input]],
    output_filenames=[args.output],
    folds=(0, 1, 2, 3, 4),
    save_npz=False,
    num_threads_preprocessing=8,
    num_threads_nifti_save=8,
    segs_from_prev_stage=None,
    do_tta=False,
    mixed_precision=True,
    overwrite_existing=True,
    all_in_gpu=False,
    step_size=0.5,
    checkpoint_name="model_final_checkpoint",
    segmentation_export_kwargs=None,
)
print("DONE:", args.output)
