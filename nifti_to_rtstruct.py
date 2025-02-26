import numpy as np
import os 
import nibabel as nib
import SimpleITK as sitk
from rt_utils import RTStructBuilder
import pydicom
import time
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
    print(np.max(empty_array))
    print(np.min(empty_array))
    print(type(empty_array))
    print(type(empty_array[0][0][0]))
    empty_array = np.rint(empty_array)
    mask_array = empty_array.astype(bool)
    
    # Add the ROI to the RTSTRUCT
    rtstruct.add_roi(
        mask=mask_array,
        color=[255, 0, 0], 
        name=roi_name
    )
    
    # Save the RTSTRUCT file
    rtstruct.save(output_path)

def combine_bone_marrow(bone_dir, output_path):
    counter = 0
    for file in os.listdir(bone_dir):

        if file.endswith('.nii.gz') and 'marrow' in file and 'spinal_cord' not in file and "assembled" not in file:
            bone_image = nib.load(os.path.join(bone_dir, file))
            if counter == 0:
                marrow_array = bone_image.get_fdata()
                counter += 1
            else:
                bone_array = bone_image.get_fdata()
                marrow_array += bone_array
    marrow_image = nib.Nifti1Image(marrow_array, affine=bone_image.affine, header=bone_image.header)
    nib.save(marrow_image, output_path)
    return marrow_array

root_dir = "/radraid/apps/personal/tfrigerio/bone_marrow_project_stuff/lunar_quant/"

if __name__ == "__main__":
    t0 = time.time()
    subdir_list = []
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if "marrow" in file and "spinal_cord" not in file and "marrow_segmentation" in subdir:
                if subdir in subdir_list:
                    continue
                list_dir = os.listdir(subdir)
                escape = False
                for item in list_dir:
                    if ".dcm" in item:
                        escape =True
                if escape:
                    continue
                print(f"Processing directory: {subdir}")
                subdir_list.append(subdir)
                previous_dir = subdir.split('/marrow_segmentation')[0]
                studyid = subdir.split('/marrow_segmentation')[0].split('/')[-1]
                print(f"Study ID: {studyid}")
                output_path = os.path.join(subdir, "assembled_marrow.nii.gz")
                marrow_array = combine_bone_marrow(subdir, output_path)
                marrow_array = nib.load(output_path).get_fdata()
                print(f"Saved assembled marrow to: {output_path}")
                rtstruct_output_path = os.path.join(subdir, studyid)
                dicom_path_list = os.listdir(previous_dir)
                
                for dicom_path in dicom_path_list:
                    if '_DICOM' in dicom_path and 'CT_' in dicom_path:
                        dicom_series_path = os.path.join(previous_dir, dicom_path)
                        print(f"Processing DICOM series: {dicom_series_path}")
                        break
            
                nifti_to_rtstruct(output_path, dicom_series_path, rtstruct_output_path, "BoneMarrow")
    t1 = time.time()
    print("time ",t1-t0)           
