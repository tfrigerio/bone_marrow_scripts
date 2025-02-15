import numpy as np
import nibabel as nib
import os
import time
from utility_functions import *

root_dir = "/radraid/apps/personal/tfrigerio/bone_marrow_project_stuff/resist_quant_data/core_data/UCLA_Lu_nifti_3D_data/"
length = len(root_dir)
if __name__ == "__main__":

    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.nii') or file.endswith('.nii.gz') and 'CT' in file:
                
                file_path = os.path.join(subdir,file)

                segmentation_dir = os.path.join(subdir, file.replace('.nii.gz','_segmentation'))
                if not os.path.exists(segmentation_dir):
                    print("Bone segmentations not found for: ", file_path)
                    continue

                segmentation_list = os.listdir(segmentation_dir)

                intermediate_dir = os.path.join(subdir, file.replace('.nii.gz','_intermediate'))
                if not os.path.exists(intermediate_dir):
                    os.makedirs(intermediate_dir)
                

                for segmentation in segmentation_list:
                    print("Processing file: ", segmentation)

                    output_path = os.path.join(intermediate_dir, segmentation.replace('.nii.gz','_dynamic_average.nii.gz'))
                    image_array = nib.load(file_path).get_fdata()
                    full_pipeline(image_array, os.path.join(segmentation_dir, segmentation), output_path, length, 0, 'average', 'scipy')

