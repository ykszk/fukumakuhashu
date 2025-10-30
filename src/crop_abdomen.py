#%%
import numpy as np
import SimpleITK as sitk
import argparse
from loguru import logger

# Peritoneal Cancer Index (PCI) segmentation (upper/mid/lower abdomen fat)

parser = argparse.ArgumentParser()
# input ct file
parser.add_argument("--input", default='../../data/example/Panoramix-cropped.nii.gz')
# total segmentator output
parser.add_argument("--total", default='../../data/example/Panoramix-cropped segmentation.seg.nrrd')
# output path
parser.add_argument("--output", default='../../data/example/abdomen_Panoramix-cropped.pci.nii.gz')
# output total segmentator file
parser.add_argument("--output_total", default='../../data/example/Panoramix-cropped.total.nii.gz')
# margin in mm
parser.add_argument("--margin", type=float, default=10.0)
args, _unknown = parser.parse_known_args()
orientation = "LPI"
# %%
img_ct = sitk.ReadImage(args.input)
img_ct = sitk.DICOMOrient(img_ct, orientation)
img_total = sitk.ReadImage(args.total)
img_total = sitk.DICOMOrient(img_total, orientation)
spacings = img_total.GetSpacing()[::-1]
arr_total = sitk.GetArrayFromImage(img_total)
# %%
import ts.total_ct as total_ct
margin_voxels = [int(args.margin / sp) for sp in spacings]
margin_z = margin_voxels[0]

# bound top
liver = arr_total==total_ct.LIVER
bound_top = np.min(np.where(liver)[0])

# bound bottom
# sacral bottom or image bottom
sacrum = arr_total==total_ct.SACRUM
if np.sum(sacrum)>0:
    bound_bottom = np.max(np.where(sacrum)[0])
else:
    bound_bottom = arr_total.shape[0]

bound_top = max(0, bound_top - margin_z)
bound_bottom = min(arr_total.shape[0], bound_bottom + margin_z)

logger.info(f"Computed cropping bounds: top={bound_top}, bottom={bound_bottom}")

# %%
img_cropped = img_ct[:, :, bound_top:bound_bottom]
sitk.WriteImage(img_cropped, args.output)
logger.info(f"Cropped abdomen saved to {args.output} with bounds {bound_top}-{bound_bottom}")
# %%
total_cropped = img_total[:, :, bound_top:bound_bottom]
sitk.WriteImage(total_cropped, args.output_total)
logger.info(f"Cropped total segmentator output saved to {args.output_total} with bounds {bound_top}-{bound_bottom}")