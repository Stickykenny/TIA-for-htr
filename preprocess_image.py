import os
import numpy as np
import cv2 as cv
import logging
logger = logging.getLogger("align_logger")


def detect_split(gray_img):

    center_dist = 0.05

    width = gray_img.shape[1]
    gray_img = gray_img[:, int(width*(0.5-center_dist))
                               :int(width*(0.5+center_dist))]
    tmp_avg = np.average(gray_img, axis=0)
    N = 10
    column_avg = [np.average([tmp_avg[n:n+N]])
                  for n in range(0, len(tmp_avg)-60, N)]

    diff = [round(abs(column_avg[i]-column_avg[i-1]), 4)
            for i in range(1, len(column_avg))]

    max_diff = np.argmax(diff)*N

    return max_diff+int(width*(0.5-center_dist))


def split_image(image_filepath):
    img = cv.imread(image_filepath)

    if img.shape[0] > img.shape[1]:
        return False
    else:
        gray_img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

        split_x = detect_split(gray_img)
        # cv.line(img, (split_x,0), (split_x,img.shape[0]), color=(0,0,255), thickness=20)

        # Left Image
        cv.imwrite(image_filepath[:-4]+"_left.jpg", img[:, 0:split_x])

        # Right Image
        cv.imwrite(image_filepath[:-4]+"_right.jpg",
                   img[:, split_x:img.shape[1]])

        os.remove(image_filepath)

        return True


def batch_preprocess(maindir):

    image_split_count = 0
    for directory, sub, files in os.walk(maindir):
        for image in files:
            image_filepath = os.path.join(directory, image)
            if split_image(image_filepath):
                logger.debug("Splitted "+image_filepath)
                image_split_count += 1

    logger.info("Splitted a total of "+str(image_split_count)+" images")
