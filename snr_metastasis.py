import nibabel as nib
import numpy as np
import os

def load_image(image_path):
    image = nib.load(image_path)
    image_array = image.get_fdata()
    return image, image_array

def threshold_image(image_array, threshold_up, threshold_down):
    bone_array_mask = np.zeros(image_array.shape)
    #bone_array_mask[image_array < threshold_up] = 1
    bone_array_mask[image_array >= threshold_down] = 1
    return bone_array_mask

root_dir = "/radraid/apps/personal/tfrigerio/bone_marrow_project_stuff/resist_quant_data/core_data/UCLA_Lu_nifti_3D_data/"
# studylist = os.listdir(data_dir)
# studylist = [i for i in studylist if 'no_quant' not in i]

if __name__ == "__main__":

    for subdir, _, files in os.walk(root_dir):
        for scan in files:

            if scan.endswith('.nii.gz') and 'PT' in scan and 'resized' in scan and 'metastasis' not in scan:
                print("Processing file: ", scan)
                file_path = os.path.join(subdir, scan)

                image, image_array = load_image(file_path)
 
                snr_array = image_array/np.std(image_array)
                metastsis_array = threshold_image(snr_array, 10000000000000000000, 5)
                metastasis_image = nib.Nifti1Image(metastsis_array, affine=None, header=image.header)
                nib.save(metastasis_image, os.path.join(file_path.replace('resized.nii.gz', 'metastasis_snr.nii.gz')))
                print("Found and processed file: ", file_path)