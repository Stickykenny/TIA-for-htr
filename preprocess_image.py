import os
import numpy as np
import cv2 as cv
from PIL import Image
from monitoring import timeit
import ujson
import logging
logger = logging.getLogger("TIA_logger")
image_extension = (".jpg", ".png")

def detect_split(gray_img: Image, center_dist: int = 0.05, steps: int = 10) -> int:
    """
    Will try to find the page split by finding the column with the most sudden change (often due to the double page fold)

    Parameters :
        gray_img :
            Numpy Array representing the gray image
        center_dist :
            Distance from the center to search the split (in percent of total image width)
        steps :
            Number of pixels regrouped to be considered a column

    Returns :
        The x coordinate of the split
    """

    width = gray_img.shape[1]

    gray_img = gray_img[:, int(width*(0.5-center_dist)):int(width*(0.5+center_dist))]

    # Get the average of each individual column
    tmp_avg = np.average(gray_img, axis=0)

    # Get the average of these column regrouped every steps
    column_avg = [np.average([tmp_avg[n:n+steps]])
                  for n in range(0, len(tmp_avg)-steps, steps)]

    # Calculate the difference between of value of each column
    diff = [round(abs(column_avg[i]-column_avg[i-1]), 4)
            for i in range(1, len(column_avg))]

    # Get the column with the most difference
    max_diff = np.argmax(diff)*steps

    return max_diff+int(width*(0.5-center_dist))


def split_image(image_filepath: str, split_status_path) -> bool:
    """
    Split double page into single pages, sufix with "_left" and "_right"

    Parameters :
        image_filepath :
            Filepath to the image

    Returns :
        True if the image was split, False if not split
    """

    if image_filepath.endswith("_right.jpg") or image_filepath.endswith("_left.jpg"):
        # Does not split already splitted images
        return False

    if os.path.exists(image_filepath[:-4]+"_right.jpg") and os.path.isfile(image_filepath[:-4]+"_right.jpg"):
        # Do nothing if splitted files already exists
        # Remove the original file
        os.remove(image_filepath)
        return False

    img = cv.imread(image_filepath)
    # If height > width, then it is not a double page
    if img.shape[1] > img.shape[0]:
        double_page = False
    else:
        double_page = True

    if double_page:

        # Case : single page
        # Add it to the dictionnary with value of 0
        with open(split_status_path, 'r', encoding='UTF-8', errors="ignore") as f:
            split_status = ujson.load(f)
        split_status[image_filepath] = 0
        with open(split_status_path, 'w', encoding='UTF-8', errors="ignore") as f:
            ujson.dump(split_status, f, indent=4)
        return False
    else:
        # Find the split location
        gray_img = cv.imread(image_filepath, cv.IMREAD_GRAYSCALE)
        split_x = detect_split(gray_img)

        # Left Image
        cv.imwrite(image_filepath[:-4]+"_left.jpg", img[:, 0:split_x])

        # Right Image
        cv.imwrite(image_filepath[:-4]+"_right.jpg",
                   img[:, split_x:img.shape[1]])

        # Remove the original file
        os.remove(image_filepath)

        # Case : double page
        # Add splitted part into a dictionnary with value of 2 and 3
        # Also add the original with value of 1 so he can be found in checklist
        with open(split_status_path, 'r', encoding='UTF-8', errors="ignore") as f:
            split_status = ujson.load(f)
        split_status[image_filepath] = 1
        split_status[image_filepath[:-4]+"_left.jpg"] = 2
        split_status[image_filepath[:-4]+"_right.jpg"] = 3
        with open(split_status_path, 'w', encoding='UTF-8', errors="ignore") as f:
            ujson.dump(split_status, f, indent=4)

        return True


@timeit
def batch_preprocess(maindir: str) -> None:
    """
    Apply all preprocessing to all files in directory

    Parameters :
        maindir :
            Directory where all images are located

    Returns :
        None
    """

    # Using a dictionnary as a checkpoint to know if an image was already processed
    # Each value means a different case
    # { 0: no need to split, 1 : already splitted,  2 : left split, 3 : right split }
    split_status_path = "tmp"+os.sep+"save"+os.sep+"split_status.json"
    if not os.path.exists(split_status_path):
        split_status = dict()
        with open(split_status_path, "w", encoding='UTF-8', errors="ignore") as file:
            ujson.dump(split_status, file, indent=4)
    else:
        with open(split_status_path, 'r', encoding='UTF-8', errors="ignore") as f:
            split_status = ujson.load(f)

    # For each image in the extract_img directory
    image_split_count = 0
    for directory, sub, files in os.walk(maindir):
        for image in files:

            # Skip non image file
            if not image.lower().endswith(image_extension):
                continue
            image_filepath = os.path.join(directory, image)

            # If the file is not already processed for splitting
            if image_filepath not in split_status:
                if split_image(image_filepath, split_status_path):
                    logger.debug("Splitted "+image_filepath)
                    image_split_count += 1

            # If the original file splitted is still present, remove it
            elif split_status[image_filepath] == 1:
                os.remove(image_filepath)

    logger.info("Splitted a total of "+str(image_split_count)+" images")
