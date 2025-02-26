import numpy as np
import os 
import nibabel as nib

def subtract_metastasis(bone_image, metastasis_image):
    bone_array = bone_image.get_fdata()
    metastasis_array = metastasis_image.get_fdata()
    if len(metastasis_array.shape) == 4:
        metastasis_array = metastasis_array[:, :, :, 0]
    bone_array[metastasis_array == 1] = 0
    bone_image = nib.Nifti1Image(bone_array, affine=bone_image.affine, header=bone_image.header)
    return bone_image

root_dir = "/radraid/apps/personal/tfrigerio/bone_marrow_project_stuff/lunar_quant"

if __name__ == "__main__":
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.nii.gz') and '_intermediate' in subdir and 'dynamic_average' in file:

                previous_dir = subdir.split('/CT_')[0]
                output_dir = os.path.join(previous_dir, 'marrow_segmentation')
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                for metastasis_file in os.listdir(previous_dir):
                    if 'metastasis_snr' in metastasis_file:
                        metastasis_image = nib.load(os.path.join(previous_dir, metastasis_file))
                        bone_image = nib.load(os.path.join(subdir, file))
                        bone_image = subtract_metastasis(bone_image, metastasis_image)
                        output_path = os.path.join(output_dir, file.replace('dynamic_average', 'marrow'))
                        nib.save(bone_image, output_path)
                        print(f"Saved file: {output_path}")
