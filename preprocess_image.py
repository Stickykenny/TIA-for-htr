import os
import numpy as np
import cv2 as cv
import logging
logger = logging.getLogger("TIA_logger")


def detect_split(gray_img: np.ndarray, center_dist: int = 0.05, steps: int = 10) -> int:
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

    gray_img = gray_img[:, int(width*(0.5-center_dist))
                               :int(width*(0.5+center_dist))]

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


def split_image(image_filepath: str) -> bool:
    """
    Split double page into single pages, sufix with "_left" and "_right"

    Parameters :
        image_filepath : 
            Filepath to the image

    Returns :
        True if the image was split, False if not split
    """
    img = cv.imread(image_filepath)

    # If height > width, then it is not a double page
    if img.shape[0] > img.shape[1]:
        return False
    else:
        # Find the split location
        gray_img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        split_x = detect_split(gray_img)

        # Left Image
        cv.imwrite(image_filepath[:-4]+"_left.jpg", img[:, 0:split_x])

        # Right Image
        cv.imwrite(image_filepath[:-4]+"_right.jpg",
                   img[:, split_x:img.shape[1]])

        # Remove the original file
        os.remove(image_filepath)

        return True


def batch_preprocess(maindir: str) -> None:
    """
    Apply all preprocessing to all files in directory

    Parameters :
        maindir : 
            Directory where all images are located

    Returns :
        None
    """

    image_split_count = 0
    for directory, sub, files in os.walk(maindir):
        for image in files:
            image_filepath = os.path.join(directory, image)
            if split_image(image_filepath):
                logger.debug("Splitted "+image_filepath)
                image_split_count += 1

    logger.info("Splitted a total of "+str(image_split_count)+" images")
