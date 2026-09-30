#%%
import matplotlib
import SimpleITK as sitk
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--image", default='../../data/example/Panoramix-cropped.nii.gz')
parser.add_argument("--total", default='../../data/example/Panoramix-cropped segmentation.seg.nrrd')
parser.add_argument("--muscle_fat", default='../../data/example/Panoramix-cropped.muscle_fat.nii.gz')
parser.add_argument("--pci", default='../../data/example/Panoramix-cropped.pci.nii.gz')
# output image path
parser.add_argument("--output", default='../../data/example/visualize_segmentation.png')

# image_path = "../../data/example/Panoramix-cropped.nii.gz"
args, _unknown = parser.parse_known_args()
image_path = args.image
image = sitk.ReadImage(image_path)
orientation = "LPI"
image = sitk.DICOMOrient(image, orientation)
# total_path = "../../data/example/Panoramix-cropped segmentation.seg.nrrd"
total_path = args.total
total = sitk.ReadImage(total_path)
total = sitk.DICOMOrient(total, orientation)
# muscle_fat_path = "../../data/example/Panoramix-cropped.muscle_fat.nii.gz"
muscle_fat_path = args.muscle_fat
muscle_fat = sitk.ReadImage(muscle_fat_path)
muscle_fat = sitk.DICOMOrient(muscle_fat, orientation)
# pci_path = "../../data/example/Panoramix-cropped.pci.nii.gz"
pci_path = args.pci
pci = sitk.ReadImage(pci_path)
pci = sitk.DICOMOrient(pci, orientation)

#%%
import matplotlib.pyplot as plt
window_level = 50
window_width = 1000
window_min = window_level - (window_width / 2)
window_max = window_level + (window_width / 2)
image_array = sitk.GetArrayFromImage(sitk.IntensityWindowing(image,
                                                              windowMinimum=window_min,
                                                              windowMaximum=window_max))
total = sitk.GetArrayFromImage(total)
muscle_fat = sitk.GetArrayFromImage(muscle_fat)
pci = sitk.GetArrayFromImage(pci)
#%%
import ts.total_ct as total_ct
import numpy as np
# calculate center of mass
def compute_center_of_mass(binary_mask):
    coords = np.nonzero(binary_mask)
    center = [int(np.mean(coords[0])),
              int(np.mean(coords[1])),
              int(np.mean(coords[2]))]
    return center
liver_center = compute_center_of_mass(total==total_ct.LIVER)
ts_center = compute_center_of_mass(np.logical_and(total_ct.VERTEBRAE_T12 <= total, total <= total_ct.VERTEBRAE_T1))
# kidney_left_center = compute_center_of_mass(total==total_ct.KIDNEY_LEFT)
kidney_left_top = np.where(total==total_ct.KIDNEY_LEFT)[0].min()


#%%
spacings = image.GetSpacing()[::-1]  # reverse to z,y,x
cmap_segments = 'tab20'
# %%
from matplotlib import colormaps
import matplotlib.colors
tab20_colors = colormaps['tab20'].colors
total_colors = np.array(tab20_colors * 6)
# add alpha channel
total_colors = np.concatenate([total_colors, np.ones((total_colors.shape[0],1))], axis=1)
# set first color (background) to transparent
total_colors[0,:] = np.array([0,0,0,0])
total_cmap = matplotlib.colors.ListedColormap(total_colors)

# crop each view to the body (from the tissue mask) plus a margin, so panels
# aren't dominated by empty black background / scanner table
margin_mm = 20

def bbox_from_mask(mask2d, margin_px_row, margin_px_col):
    rows = np.any(mask2d, axis=1)
    cols = np.any(mask2d, axis=0)
    if not rows.any() or not cols.any():
        return slice(None), slice(None)
    r0, r1 = np.where(rows)[0][[0, -1]]
    c0, c1 = np.where(cols)[0][[0, -1]]
    r0 = max(0, r0 - margin_px_row)
    r1 = min(mask2d.shape[0], r1 + margin_px_row + 1)
    c0 = max(0, c0 - margin_px_col)
    c1 = min(mask2d.shape[1], c1 + margin_px_col + 1)
    return slice(r0, r1), slice(c0, c1)

ref_indexes = [kidney_left_top, liver_center[1], ts_center[2]]
aspects = [spacings[1]/spacings[2], spacings[0]/spacings[2], spacings[0]/spacings[1]]
# (row_spacing, col_spacing) for each view, matching the axes selected by `index` below
row_col_spacings = [(spacings[1], spacings[2]), (spacings[0], spacings[2]), (spacings[0], spacings[1])]
view_names = ['Axial', 'Coronal', 'Sagittal']
plt.figure(figsize=(10,10))
for i, slice_index in enumerate(ref_indexes):
    aspect = aspects[i]
    view_name = view_names[i]
    if view_name == 'Axial':
        index = (slice_index, slice(None), slice(None))
    elif view_name == 'Coronal':
        index = (slice(None), slice_index, slice(None))
    elif view_name == 'Sagittal':
        index = (slice(None), slice(None), slice_index)

    row_sp, col_sp = row_col_spacings[i]
    margin_row_px = round(margin_mm / row_sp)
    margin_col_px = round(margin_mm / col_sp)
    row_slice, col_slice = bbox_from_mask(muscle_fat[index] > 0, margin_row_px, margin_col_px)
    crop = (row_slice, col_slice)

    ct_view = image_array[index][crop]
    total_view = total[index][crop]
    muscle_fat_view = muscle_fat[index][crop]
    pci_view = pci[index][crop]

    # ct image
    plt.subplot(3, 4, i*4+1)
    plt.imshow(ct_view, cmap='gray', aspect=aspect)
    plt.title("CT")
    plt.axis('off')
    # ct image with segmentation overlay
    plt.subplot(3, 4, i*4+2)
    plt.imshow(ct_view, cmap='gray', aspect=aspect)
    plt.imshow(total_view, cmap=total_cmap, alpha=0.5, aspect=aspect, interpolation='none')
    plt.title("TotalSegmentator")
    plt.axis('off')
    # ct image with muscle/fat overlay
    plt.subplot(3, 4, i*4+3)
    plt.imshow(ct_view, cmap='gray', aspect=aspect)
    plt.imshow(muscle_fat_view, cmap=total_cmap, alpha=0.8, aspect=aspect, interpolation='none')
    plt.title("Muscle/Fat")
    plt.axis('off')
    # ct image with pci overlay
    plt.subplot(3, 4, i*4+4)
    plt.imshow(ct_view, cmap='gray', aspect=aspect)
    plt.imshow(pci_view, cmap='hot', alpha=0.7, aspect=aspect, interpolation='none')

    plt.title("PCI")
    plt.axis('off')

plt.tight_layout()
plt.savefig(args.output, dpi=300)
# %%