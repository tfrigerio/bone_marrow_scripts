import numpy as np 
import nibabel as nib
from scipy.ndimage import binary_opening, binary_erosion
import time


HEADER_KEYS = ['pixdim', 'xyzt_units', 'qform_code', 'sform_code', 'quatern_b', 'quatern_c', 'quatern_d', 'qoffset_x', 'qoffset_y', 'qoffset_z', 'srow_x', 'srow_y', 'srow_z']

# Loading the bone mask as a nifti image and as an array
def load_bone_mask(bone_mask_path):
    bone_mask = nib.load(bone_mask_path)                #the nifti mask is necessary to retain the header information
    bone_mask_array = bone_mask.get_fdata()
    return bone_mask, bone_mask_array

# Isolating the bone from the image, returning an array with 0 values outside the bone
def isolate_bone_on_image(image_array, bone_mask_array):
    return image_array * bone_mask_array

# Obtaining the upper threshold for the bone marrow segmentation
def obtain_upper_threshold(image_array, bone_mask_array, offset, mode):
    values = image_array[bone_mask_array==1]
    #Check which thresholding mode is selected
    match mode:
        #For static thresholding, the offset is used as the threshold
        case 'static':
            return offset
        
        #For dynamic thresholding, the offset is applied to a known bone marrow value (the 5th percentile)
        case 'dynamic':
            if np.any(values) != 0:
                fifth_percentile = np.percentile(values, 5)
                threshold = fifth_percentile + offset
                return threshold
            return 0

        #For average thresholding, the average of the 5th and 95th percentiles is used as the threshold, offset is not used
        case 'average':
            if np.any(values) != 0:
                fifth_percentile = np.percentile(values, 5)
                ninety_fifth_percentile = np.percentile(values, 95)
                threshold = (0.7*fifth_percentile + 0.3*ninety_fifth_percentile)
                return threshold
            return 0

# Thresholding the bone marrow using the obtained threshold, returning a binary mask
def threshold_segmentation_of_bone_marrow(bone_array, threshold_up, threshold_down, bone_mask_array, opening):
    bone_marrow_array_mask = np.where((bone_array < threshold_up) & (bone_array > threshold_down), 1, 0)*bone_mask_array
    return bone_marrow_array_mask


#Perform binary opening to get rid of small noise as well as soft tissue just outside of the cortical bone
def opening_3D(bone_marrow_array_mask, iterations, opening):
    opened = binary_opening(bone_marrow_array_mask, iterations=iterations)
    return opened
          

    
# The segmented bone's header is inherited by the bone marrow mask
def header_processing(bone_marrow_array_mask,bone_mask):
    nifti_mask = nib.Nifti1Image(bone_marrow_array_mask, affine=None, header=bone_mask.header)
    # This next step shouldn't be necessary, but it seems to prevent some unexpected failures
    for key in HEADER_KEYS:
        nifti_mask.header[key]=bone_mask.header[key]
 
    return nifti_mask

#Saves a nifti image to a .nii.gz file
def save_masks(connected_components, output_path):
    nib.save(connected_components, output_path)

#Full pipeline applies thresholding to find the bone marrow of a bone mask of specified path onto an image passed as a numpy array
#There are 3 modes available: 'dynamic', 'static', 'average' with regard to obtaining the upper threshold

def full_pipeline(image_array, bone_mask_path, output_path, length, offset, mode, opening):

    t0 = time.time()
    bone_mask, bone_mask_array = load_bone_mask(bone_mask_path)
    t1 = time.time()
    print('image_shape: ', image_array.shape)
    print('Time to load image and bone mask: ', t1-t0)

    t2 = time.time()
    
    if image_array.shape != bone_mask_array.shape:
        if image_array.shape[-1] == 1:
            image_array = image_array[:, :, :, 0]
        else:
            raise ValueError('Image and mask have different shapes')
    
    t3 = time.time()
    print('Time to check shapes: ', t3-t2)

    t4 = time.time()
    bone_array = isolate_bone_on_image(image_array, bone_mask_array)
    t5 = time.time()
    print('Time to isolate bone on image: ', t5-t4)

    t6 = time.time()
    upper_threshold = obtain_upper_threshold(image_array, bone_mask_array, offset, mode)
    t7 = time.time()
    print('Time to obtain upper threshold: ', t7-t6)

    t8 = time.time()
    bone_marrow_array_mask = threshold_segmentation_of_bone_marrow(bone_array, upper_threshold, -100, bone_mask_array, opening)
    t9 = time.time()
    print('Time to threshold segmentation of bone marrow: ', t9-t8)

    t10 = time.time()
    if np.max(np.shape(image_array))>= 100 :
        bone_marrow_array_mask = opening_3D(bone_marrow_array_mask, 1, opening)
    t11 = time.time()
    print('Time to open 3D: ', t11-t10)
    eroded_bone_array = np.zeros(bone_marrow_array_mask.shape)
    for slice in range(bone_marrow_array_mask.shape[2]):
        eroded_bone_array[:,:,slice] = binary_erosion(bone_marrow_array_mask[:,:,slice])
    bone_marrow_array_mask = eroded_bone_array*bone_marrow_array_mask
    t12 = time.time()
    connected_components = header_processing(bone_marrow_array_mask, bone_mask)
    t13 = time.time()
    print('Time to process header: ', t13-t12)

    t14 = time.time()
    save_masks(connected_components, output_path)
    t15 = time.time()
    print('Time to save masks: ', t15-t14)
    return print(bone_mask_path[length:])