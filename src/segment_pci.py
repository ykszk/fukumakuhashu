# %%
import numpy as np
import SimpleITK as sitk
import argparse

# Peritoneal Cancer Index (PCI) segmentation (upper/mid/lower abdomen fat)

parser = argparse.ArgumentParser()
# total segmentator output
parser.add_argument("--total", default='../../data/example/Panoramix-cropped segmentation.seg.nrrd')
# muscle fat output
parser.add_argument("--muscle_fat", default='../../data/example/Panoramix-cropped.muscle_fat.nii.gz')
# output path
parser.add_argument("--output", default='../../data/example/Panoramix-cropped.pci.nii.gz')

args, _unknown = parser.parse_known_args()

img_total = sitk.ReadImage(args.total)
img_muscle_fat = sitk.ReadImage(args.muscle_fat)
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
L_FAT = 3
arr_fat = arr_muscle_fat==L_FAT
plt.imshow(arr_fat[:, col_slice], cmap='gray')
# %%

# Divide into three parts: upper, middle, lower
# upper: liver top to lower costal arch
# middle: lower costal arch to iliac crest
# lower: iliac crest to public sympysis (but use lower sacram as a proxy)

from ts import total_ct
import cc3d

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
sitk.WriteImage(img_pci_fat, args.output)

# %%
