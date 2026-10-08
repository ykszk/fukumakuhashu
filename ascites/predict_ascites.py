import argparse
import os


class _ListQueue(list):
    put = list.append


def _preprocess_in_process(trainer, list_of_lists, output_files, num_processes=2, segs_from_prev_stage=None):
    # Drop-in for nnunet's preprocess_multithreaded that runs its preprocess_save_to_queue
    # in this process instead of a child. The child Process needs the trainer pickled,
    # which fails on Windows (spawn) because nnU-Net v1's trainer/network hold lambdas.
    from nnunet.inference.predict import preprocess_save_to_queue

    if segs_from_prev_stage is None:
        segs_from_prev_stage = [None] * len(list_of_lists)
    q = _ListQueue()
    preprocess_save_to_queue(
        trainer.preprocess_patient, q, list_of_lists, output_files, segs_from_prev_stage,
        list(range(1, trainer.num_classes)), trainer.plans["transpose_forward"],
    )
    for item in q:
        if item != "end":
            yield item


def main():
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

    predict.preprocess_multithreaded = _preprocess_in_process

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


# nnU-Net spawns worker processes; on Windows (spawn start method) each worker
# re-imports this module, so the entry point must be guarded.
if __name__ == "__main__":
    main()
