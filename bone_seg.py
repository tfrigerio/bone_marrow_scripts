import os
import nibabel as nib
from totalsegmentator.python_api import totalsegmentator
import xmltodict

bones = [
    "clavicula_left",
    "clavicula_right",
    "hip_left",
    "hip_right",
    "femur_left",
    "femur_right",
    "humerus_left",
    "humerus_right",
    "rib_left_1",
    "rib_left_2",
    "rib_left_3",
    "rib_left_4",
    "rib_left_5",
    "rib_left_6",
    "rib_left_7",
    "rib_left_8",
    "rib_left_9",
    "rib_left_10",
    "rib_left_11",
    "rib_left_12",
    "rib_right_1",
    "rib_right_2",
    "rib_right_3",
    "rib_right_4",
    "rib_right_5",
    "rib_right_6",
    "rib_right_7",
    "rib_right_8",
    "rib_right_9",
    "rib_right_10",
    "rib_right_11",
    "rib_right_12",
    "sacrum",
    "scapula_left",
    "scapula_right",
    "skull",
    "spinal_cord",
    "sternum",
    "vertebrae_L1",
    "vertebrae_L2",
    "vertebrae_L3",
    "vertebrae_L4",
    "vertebrae_L5",
    "vertebrae_S1",
    "vertebrae_T1",
    "vertebrae_T2",
    "vertebrae_T3",
    "vertebrae_T4",
    "vertebrae_T5",
    "vertebrae_T6",
    "vertebrae_T7",
    "vertebrae_T8",
    "vertebrae_T9",
    "vertebrae_T10",
    "vertebrae_T11",
    "vertebrae_T12"
]

def get_multilabel_nifti_header(img):
    ext_header = img.header.extensions[0].get_content()
    ext_header = xmltodict.parse(ext_header)
    ext_header = ext_header["CaretExtension"]["VolumeInformation"]["LabelTable"]["Label"]
    if isinstance(ext_header, dict):
        ext_header = [ext_header]
        
    label_map = {int(e["@Key"]): e["#text"] for e in ext_header}
    return img, label_map

def segment_nifti_files(root_dir):
    # Initialize the TotalSegmentator
    # Walk through the directory tree
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.nii') or file.endswith('.nii.gz') and 'CT' in file:
                file_path = os.path.join(subdir, file)
                print(f"Processing file: {file_path}")
                segmented_file_path = os.path.join(subdir, f"{file.replace('.nii.gz','')}_segmentation")
                if not os.path.exists(segmented_file_path):
                    os.makedirs(segmented_file_path)
                
                image = nib.load(file_path)
                masks = totalsegmentator(image)
                masks_without_header, labels = get_multilabel_nifti_header(masks)
                flipped_labels = {v: k for k, v in labels.items()}
                print(f"Labels: {flipped_labels}")
                for bone in bones:
                    mask = masks_without_header.get_fdata() == flipped_labels[bone]
                    mask = mask.astype(int)
                    mask = nib.Nifti1Image(mask, affine=None, header=masks_without_header.header)
                    segmented_file_path_bone = os.path.join(segmented_file_path, f"{bone}.nii.gz")
                    nib.save(mask, segmented_file_path_bone)
                    print(f"Segmented file saved: {segmented_file_path_bone}")


                # Save the segmented image
                print(f"Segmented file saved: {segmented_file_path}")

if __name__ == "__main__":
    root_directory = "/radraid/apps/personal/tfrigerio/bone_marrow_project_stuff/resist_quant_data/core_data/UCLA_Lu_nifti_3D_data/"
    segment_nifti_files(root_directory)