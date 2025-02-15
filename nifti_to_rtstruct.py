import numpy as np
import os 
import nibabel as nib
import SimpleITK as sitk
from rt_utils import RTStructBuilder

def nifti_to_rtstruct(nifti_path, dicom_series_path, output_path, roi_name="Segmentation"):

    # Load the NIFTI mask
    nifti_mask = sitk.ReadImage(nifti_path)
    mask_array = sitk.GetArrayFromImage(nifti_mask)
    
    # Load mask with nibabel
    nifti_mask = nib.load(nifti_path)
    mask_array = nifti_mask.get_fdata()
    # Invert x and y axes
    empty_array = np.zeros_like(mask_array)
    for i in range(empty_array.shape[0]):
        empty_array[i] = mask_array[:,i,:]
    # Create RT Struct object
    rtstruct = RTStructBuilder.create_new(dicom_series_path)
    
    # Add ROI from the binary mask
    # Note: mask_array needs to be boolean
    mask_array = empty_array.astype(bool)
    
    # Add the ROI to the RTSTRUCT
    rtstruct.add_roi(
        mask=mask_array,
        color=[255, 0, 0],  # Red color for visualization
        name=roi_name
    )
    
    # Save the RTSTRUCT file
    rtstruct.save(output_path)

def combine_bone_marrow(bone_dir, output_path):
    counter = 0
    for file in os.listdir(bone_dir):

        if file.endswith('.nii.gz') and 'marrow' in file and 'spinal_cord' not in file:
            bone_image = nib.load(os.path.join(bone_dir, file))
            if counter == 0:
                marrow_array = bone_image.get_fdata()
                counter += 1
            else:
                bone_array = bone_image.get_fdata()
                marrow_array += bone_array
    marrow_image = nib.Nifti1Image(marrow_array, affine=bone_image.affine, header=bone_image.header)
    nib.save(marrow_image, output_path)

root_dir = "/radraid/apps/personal/tfrigerio/bone_marrow_project_stuff/resist_quant_data/core_data/UCLA_Lu_nifti_3D_data/"

if __name__ == "__main__":
    subdir_list = []
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if "marrow" in file and "spinal_cord" not in file and "marrow_segmentation" in subdir:
                if subdir in subdir_list:
                    continue
                print(f"Processing directory: {subdir}")
                subdir_list.append(subdir)
                output_path = os.path.join(subdir, "assembled_marrow.nii.gz")
                combine_bone_marrow(subdir, output_path)
                print(f"Saved assembled marrow to: {output_path}")
                rtstruct_output_path = os.path.join(subdir, "rtstruct")
                previous_dir = subdir.split('/marrow_segmentation')[0]
                dicom_path_list = os.listdir(previous_dir)
                print(f"Previous dir: {previous_dir}")
                for dicom_path in dicom_path_list:
                    if 'Body' in dicom_path:
                        dicom_series_path = os.path.join(previous_dir, dicom_path)
                        break
                
                nifti_to_rtstruct(output_path, dicom_series_path, rtstruct_output_path, "BoneMarrow")
                
