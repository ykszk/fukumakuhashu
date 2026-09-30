# %%
import numpy as np
import SimpleITK as sitk
import argparse
from loguru import logger
from scipy import ndimage

# Peritoneal Cancer Index (PCI) segmentation (upper/mid/lower abdomen fat)

parser = argparse.ArgumentParser()
# total segmentator output
parser.add_argument("--total", default='../../data/example/Panoramix-cropped segmentation.seg.nrrd')
# tissue segmentation output (TotalSegmentator tissue_4_types)
parser.add_argument("--muscle_fat", default='../../data/example/Panoramix-cropped.muscle_fat.nii.gz')
# output path
parser.add_argument("--output", default='../../data/example/Panoramix-cropped.pci.nii.gz')
# output path for the "remove" mask (non-fat regions cleared from the fat mask)
parser.add_argument("--remove_output", default='../../data/example/Panoramix-cropped.remove.nii.gz')
# margin (mm) to shrink digestive organs by before excluding them, so perivisceral/mesenteric
# fat immediately adjacent to bowel/stomach isn't accidentally stripped out
parser.add_argument("--digestive_shrink_mm", type=float, default=1.0)

args, _unknown = parser.parse_known_args()
orientation = "LPS"

img_total = sitk.ReadImage(args.total)
original_orientation = sitk.DICOMOrientImageFilter.GetOrientationFromDirectionCosines(img_total.GetDirection())
img_total = sitk.DICOMOrient(img_total, orientation)

img_muscle_fat = sitk.ReadImage(args.muscle_fat)
img_muscle_fat = sitk.DICOMOrient(img_muscle_fat, orientation)

arr_total = sitk.GetArrayFromImage(img_total)
arr_muscle_fat = sitk.GetArrayFromImage(img_muscle_fat)
#%%
arr_total.shape, arr_muscle_fat.shape
# %%
import matplotlib.pyplot as plt

col_slice = 200
plt.imshow(arr_total[:, col_slice], cmap='tab20')
plt.colorbar()
# %%
plt.imshow(arr_muscle_fat[:, col_slice], cmap='tab20')
plt.colorbar()
#%%
from ts import total_ct
import cc3d

# Build a "remove" mask from TotalSegmentator's `total` labels to clear non-fat
# regions (organs, bone, vessels, muscle, etc.) that leak into the fat mask.
#
# Solid/well-defined structures (liver, kidneys, spleen, bone, muscle, vessels, ...)
# are excluded wholesale: any voxel TotalSegmentator assigned to one of them can
# never legitimately be fat.
#
# Digestive-tract organs (stomach, small bowel, duodenum, colon, esophagus) are
# treated differently: their lumen/wall segmentation is looser and variable
# (peristalsis, filling state, partial volume), and a lot of clinically relevant
# perivisceral/mesenteric fat sits immediately adjacent to bowel. Excluding the
# full digestive mask would strip that fat too, so it's shrunk by a margin first
# and only the eroded "core" is added to `remove`.
DIGESTIVE_LABELS = [
    total_ct.ESOPHAGUS,
    total_ct.STOMACH,
    total_ct.SMALL_BOWEL,
    total_ct.DUODENUM,
    total_ct.COLON,
]
digestive_mask = np.isin(arr_total, DIGESTIVE_LABELS)
non_digestive_mask = (arr_total > 0) & ~digestive_mask

spacing_zyx = img_total.GetSpacing()[::-1]
digestive_dist = ndimage.distance_transform_edt(digestive_mask, sampling=spacing_zyx)
digestive_eroded = digestive_dist > args.digestive_shrink_mm

# remove labels: 1=non-digestive (organs/bone/vessels/muscle), 2=digestive organs (eroded core)
remove = np.zeros_like(arr_total, dtype=np.uint8)
remove[non_digestive_mask] = 1
remove[digestive_eroded] = 2

img_remove = sitk.GetImageFromArray(remove)
img_remove.CopyInformation(img_total)
img_remove = sitk.DICOMOrient(img_remove, original_orientation)
sitk.WriteImage(img_remove, args.remove_output)
logger.info(f"Remove mask saved to {args.remove_output}")

#%%
# tissue_4_types labels: 1=subcutaneous_fat, 2=torso_fat (VAT), 3=skeletal_muscle, 4=intermuscular_fat
L_FAT = 2
arr_fat = (arr_muscle_fat==L_FAT) & (remove == 0)
plt.imshow(arr_fat[:, col_slice], cmap='gray')
# %%

# Divide into three parts: upper, middle, lower
# upper: liver top to lower costal arch
# middle: lower costal arch to iliac crest
# lower: iliac crest to public sympysis (but use lower sacram as a proxy)

liver = arr_total==total_ct.LIVER
liver_indices = np.where(liver)
liver_top = np.max(liver_indices[0])

# lower costal arch: use lowest rib
# left_costal_arch = arr_total == total_ct.RIB_LEFT_10
# left_ca_indices = np.where(left_costal_arch)
# right_costal_arch = arr_total == total_ct.RIB_RIGHT_10
# right_ca_indices = np.where(right_costal_arch)
costal_arch = arr_total == total_ct.COSTAL_CARTILAGES
costal_arch = cc3d.largest_k(costal_arch, 2) # keep two largest components (should be left and right)
costal_arch = costal_arch > 0
costal_arch_indices = np.where(costal_arch)
costal_arch_bottom = np.min(costal_arch_indices[0])
# # mean of left and right rib
# costal_arch = int((np.min(left_ca_indices[0]) + np.min(right_ca_indices[0])) / 2)

#%%
plt.imshow(np.max(costal_arch, axis=1))

#%%

# iliac crest
# HIP = ILIAC
iliac = (arr_total==total_ct.HIP_LEFT) | (arr_total==total_ct.HIP_RIGHT)
iliac_indices = np.where(iliac)
iliac_crest = np.max(iliac_indices[0])
# sacrum
sacrum = arr_total==total_ct.SACRUM
sacrum_indices = np.where(sacrum)
if not sacrum_indices[0].size:
    logger.warning("Sacrum not found, using bottom slice as sacrum lower bound")
    sacrum_lower = 0 # arr_total.shape[0]-1
else:
    sacrum_lower = np.min(sacrum_indices[0])

#%%
mip = np.maximum(np.max(liver, axis=1), np.max(costal_arch, axis=1)*2)
# , np.max(iliac, axis=1)*3, np.max(sacrum, axis=1)*4)
mip = np.maximum(mip, np.max(iliac, axis=1)*3)
mip = np.maximum(mip, np.max(sacrum, axis=1)*4)
plt.imshow(mip)

#%%
pci_region = np.zeros_like(arr_fat, dtype=np.uint8)
# lower
pci_region[sacrum_lower: iliac_crest] = 1
# middle
pci_region[iliac_crest: costal_arch_bottom] = 2
# upper
pci_region[costal_arch_bottom: liver_top] = 3

plt.imshow(pci_region[:, col_slice], cmap='tab10')
plt.colorbar()

# %%
pci_fat = arr_fat * pci_region
plt.imshow(pci_fat[:, col_slice], cmap='tab10')
plt.colorbar()

# %%
img_pci_fat = sitk.GetImageFromArray(pci_fat)
img_pci_fat.CopyInformation(img_total)
img_pci_fat = sitk.DICOMOrient(img_pci_fat, original_orientation)
sitk.WriteImage(img_pci_fat, args.output)

# %%
