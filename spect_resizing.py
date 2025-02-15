import numpy as np
import os
import nibabel as nib
from scipy.ndimage import zoom

def resize_image(image, target_shape):
    factors = [t / float(s) for t, s in zip(target_shape, image.shape)]
    resized_image = zoom(image, factors, order=1)  # order=1 for bilinear interpolation
    return resized_image

def resize_nifti(image, new_shape):
    data = image.get_fdata()
    new_data = resize_image(data, new_shape)
    affine = image.affine
    zooms = np.array(image.header.get_zooms())
    new_zooms = np.array(new_shape) / np.array(data.shape)
    new_affine = np.copy(affine)
    new_affine[:3, :3] = new_affine[:3, :3] * (zooms / new_zooms)
    
    new_image = nib.Nifti1Image(new_data, new_affine)
    return new_image

root_dir = "/radraid/apps/personal/tfrigerio/bone_marrow_project_stuff/resist_quant_data/core_data/UCLA_Lu_nifti_3D_data/"

if __name__ == "__main__":

    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.nii') or file.endswith('.nii.gz') and 'PT' in file:
                file_path = os.path.join(subdir, file)

                # Find corresponding CT file
                ct_file_counter = 0
                for ct_file in files:
                    if ct_file.endswith('.nii') or ct_file.endswith('.nii.gz') and 'CT' in ct_file:
                        ct_file_path = os.path.join(subdir, ct_file)
                        ct_file_counter += 1
                if ct_file_counter != 1:
                    print(f"Error: Found {ct_file_counter} CT files for {file_path}")
                    continue
                print(f"Processing file: {file_path}")
                image = nib.load(file_path)
                ct_image = nib.load(ct_file_path)
                new_shape = ct_image.shape
                resized_image = resize_nifti(image, new_shape)
                resized_file_path = os.path.join(subdir, f"{file.replace('.nii.gz','')}_resized.nii.gz")
                nib.save(resized_image, resized_file_path)
                print(f"Resized file saved: {resized_file_path}")
