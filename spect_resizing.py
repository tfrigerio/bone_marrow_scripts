import numpy as np
import os
import nibabel as nib
from scipy.ndimage import zoom, map_coordinates


def resize_spect_to_ct(spect_path, ct_path, output_path, interpolation_order=1):
    """
    Resize a SPECT scan to match the shape and spatial coordinates of a CT scan.
    This function first aligns the scans in real-world coordinates, then crops 
    the SPECT scan accordingly, and finally resamples it to match the CT dimensions.
    
    Handles 4D SPECT data where the 4th dimension might have length 1.
    
    Parameters:
    -----------
    spect_path : str
        Path to the SPECT NIfTI file
    ct_path : str
        Path to the CT NIfTI file that will be used as the reference
    output_path : str
        Path where the resized SPECT NIfTI file will be saved
    interpolation_order : int, optional
        Order of interpolation (0: nearest, 1: linear, 3: cubic)
        Default is 1 (linear/bilinear)
    
    Returns:
    --------
    nibabel.nifti1.Nifti1Image
        The resized SPECT image as a NIfTI object
    """
    # Load the SPECT and CT NIfTI files
    spect_img = nib.load(spect_path)
    ct_img = nib.load(ct_path)
    
    # Get the affine transformations
    spect_affine = spect_img.affine
    ct_affine = ct_img.affine
    
    # Get the dimensions of the CT image (spatial dimensions only)
    ct_shape = ct_img.shape[:3]
    
    # Get the SPECT data
    spect_data = spect_img.get_fdata()
    
    # Check if SPECT is 4D with 4th dimension of length 1
    is_4d_singleton = False
    original_shape = spect_data.shape
    if len(spect_data.shape) == 4 and spect_data.shape[3] == 1:
        is_4d_singleton = True
        # Squeeze the data to make it 3D for processing
        spect_data = np.squeeze(spect_data, axis=3)
    
    # Create a grid of voxel coordinates for the CT image
    ct_grid = np.array(np.meshgrid(
        np.arange(ct_shape[0]),
        np.arange(ct_shape[1]),
        np.arange(ct_shape[2]),
        indexing='ij'
    ))
    
    # Reshape the grid to a list of voxel coordinates
    ct_voxels = ct_grid.reshape(3, -1).T
    
    # Add a column of ones for homogeneous coordinates
    ct_voxels_homog = np.hstack((ct_voxels, np.ones((ct_voxels.shape[0], 1))))
    
    # Convert CT voxel coordinates to world coordinates
    ct_world = ct_voxels_homog @ ct_affine.T
    
    # Convert world coordinates to SPECT voxel coordinates
    spect_voxels_homog = ct_world @ np.linalg.inv(spect_affine).T
    spect_voxels = spect_voxels_homog[:, :3]
    
    # Reshape the coordinates back to the grid shape for sampling
    spect_coords = spect_voxels.T.reshape(3, *ct_shape)
    
    # Sample the SPECT data at the calculated coordinates using interpolation
    resampled_spect = map_coordinates(spect_data, spect_coords, order=interpolation_order, 
                                     mode='constant', cval=0.0)
    
    # If the original was 4D with singleton dimension, restore that dimension
    if is_4d_singleton:
        resampled_spect = np.expand_dims(resampled_spect, axis=3)
    
    # Create a new NIfTI image with the resampled data and the CT affine
    resampled_img = nib.Nifti1Image(resampled_spect, ct_affine)
    
    # Copy header information from CT, but preserve certain SPECT-specific header fields if needed
    ct_header = ct_img.header.copy()
    
    # Update dimensions in the header to match the actual data
    if is_4d_singleton:
        ct_header.set_data_shape((*ct_shape, 1))
    else:
        ct_header.set_data_shape(ct_shape)
    
    # Assign the updated header
    # resampled_img.header = ct_header
    
    # Save the resampled image
    nib.save(resampled_img, output_path)
    
    print(f"Resized SPECT scan saved to {output_path}")
    print(f"Original SPECT shape: {original_shape}, New shape: {resampled_spect.shape}")
    
    return resampled_img

def resize_image(image, target_shape):
    factors = [t / float(s) for t, s in zip(target_shape, image.shape)]
    resized_image = zoom(image, factors, order=1)  # order=1 for bilinear interpolation
    return resized_image

def resize_nifti(data, affine, header, new_shape):
    # data = image.get_fdata()
    # if len(data.shape) == 4:
    #     data = data[:, :, :, 0]
    print(f"Original shape: {data.shape}")
    print(f"New shape: {new_shape}")
    new_data = resize_image(data, new_shape)
    # affine = image.affine
    # Update the affine matrix for the resized image
    # Calculate the scaling matrix that maps from new voxel space to original voxel space
    scaling = np.diag(list(np.array(data.shape) / np.array(new_shape)) + [1])

    # The new affine is the original affine multiplied by this scaling matrix
    new_affine = affine @ scaling

    
    new_zooms = np.array(new_shape) / np.array(data.shape)
    print(f"New zooms: {new_zooms}")
    # if len(zooms) == 4:
    #     zooms = zooms[:3]
  
    
    new_image = nib.Nifti1Image(new_data, affine)
    return new_image

root_dir = "/radraid/apps/personal/tfrigerio/bone_marrow_project_stuff/lunar_quant"

if __name__ == "__main__":

    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.nii') or file.endswith('.nii.gz') and 'PT' in file and 'resized' not in file:
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
                resize_spect_to_ct(file_path, ct_file_path, file_path.replace('.nii.gz', '_resized.nii.gz'))
                continue
                image = nib.load(file_path)
                ct_image = nib.load(ct_file_path)
                new_header = ct_image.header
                if len(image.shape) == 4:
                    new_image_data = image.get_fdata()[:, :, :, 0]
                else:
                    new_image_data = image.get_fdata()
                new_affine = ct_image.affine
                new_shape = ct_image.shape
                resized_image = resize_nifti(new_image_data, new_affine, new_header, new_shape)
                resized_file_path = os.path.join(subdir, f"{file.replace('.nii.gz','')}_resized.nii.gz")
                nib.save(resized_image, resized_file_path)
                print(f"Resized file saved: {resized_file_path}")
