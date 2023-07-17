from kraken import blla
from kraken import rpred
from kraken.lib import models
from PIL import Image
import cv2 as cv
import numpy as np
import os
import pickle
import logging
logger = logging.getLogger("align_logger")

model_path = 'KrakenModel/HTR-United-Manu_McFrench.mlmodel'
model = models.load_any(model_path)


def process_images(main_dir, ocr=True, crop=False):
    """
    For all images in a directory, apply segmentation, predictions and cropping

    Parameters :
        main_dir :
            Directory in which images are located
        ocr :
            If False, skip predictions
        crop :
            If True, produce all cropped segmentations images in ./cropped/

    Returns :
        None
    """
    os.makedirs("tmp"+os.sep+"save"+os.sep+"segment", exist_ok=True)
    os.makedirs("tmp"+os.sep+"save"+os.sep+"ocr_save", exist_ok=True)

    image_extension = (".jpg", ".png", ".svg", "jpeg")
    for (dirpath, subdirnames, filenames) in os.walk(main_dir):
        for filename in filenames:
            if not filename.lower().endswith(image_extension):
                # skip non-image file
                logger.debug("skipped this non-image file : "+filename)
                continue
            filepath = dirpath+os.sep+filename
            logger.info("Processing : "+filepath)
            im = Image.open(filepath)

            # Segmentations and predictions
            logger.debug("Starting segmentation")
            segment_save = "tmp"+os.sep+"save"+os.sep + \
                "segment"+os.sep+filename+'_segment.pickle'
            if not (os.path.exists(segment_save) and os.path.isfile(segment_save)):
                baseline_seg = blla.segment(im)  # Json
                with open(segment_save, 'wb') as file:
                    pickle.dump(baseline_seg, file)
            else:
                # Load saved result to save time
                with open(segment_save, 'rb') as file:
                    baseline_seg = pickle.load(file)

            logger.debug("Starting prediction")
            predictions = ""
            predict_backup = "tmp"+os.sep+"save"+os.sep + \
                "ocr_save"+os.sep+filename+'_ocr.pickle'
            if ocr:
                if not (os.path.exists(predict_backup) and os.path.isfile(predict_backup)):
                    # https://kraken.re/main/api.html#recognition
                    predictions = ocr_img(model, im, baseline_seg, filename)
                else:
                    # Load saved result to save time
                    with open(predict_backup, 'rb') as file:
                        predictions = pickle.load(file)
                    logger.debug(
                        "\tLoaded ocr from previously calculated result")

            # Cropping segmented text
            cropping(baseline_seg, filepath, predictions, crop)

            im.close()
            logger.debug("Done processing")


def ocr_img(model, im, baseline_seg,  filename):
    """
    Return and save result of applying prediction on an image

    Parameters :
        model :
            Model used for predicting
        im :
            Image PIL object
        baseline_seg :
            Segmentation data obtained from blla.segment(im)
        filename :
            Name of the image file

    Returns :
        Prediction produce by kraken.rpred.rpred
    """
    ocr_dir = 'tmp'+os.sep+'ocr_result'
    os.makedirs(ocr_dir, exist_ok=True)

    # https://kraken.re/main/api.html#recognition
    predictions = [record for record in rpred.rpred(model, im, baseline_seg)]

    ocr_filepath = ocr_dir+os.sep+filename[:-4]+'_ocr.txt'
    with open(ocr_filepath, 'w') as f:
        for record in predictions:
            logger.debug("Wrote "+record.prediction + "into "+ocr_filepath)
            f.write(record.prediction+"\n")
        logger.info("Created "+ocr_filepath)

    # Backup result to avoid time-consuming steps on relaunch
    logger.debug("Saved ocr prediction into "+"tmp"+os.sep +
                 "save"+os.sep+"ocr_save"+os.sep+filename+'_ocr.pickle')
    with open("tmp"+os.sep+"save"+os.sep+"ocr_save"+os.sep+filename+'_ocr.pickle', 'wb') as file:
        pickle.dump(predictions, file)

    return predictions


def cropping(json_data, filepath, predictions, crop=False):
    """
    Draw the segmented region on the image and if crop is True cropped image will be generated at ./cropped/

    Parameters :
        json_data :
            Segmentation data obtained from blla.segment(im)
        filepath :
            The path of the original image
        predictions :


    Return :
        A list of usable [pattern,text_matched] and his list of index indicating where these match are in the original list
    """

    img = cv.imread(filepath, cv.IMREAD_COLOR)
    filename = filepath.split(os.sep)[-1]

    cropping_dir = "cropped"+os.sep+filename
    segmented_img_dir = "tmp"+os.sep+"segmented"
    os.makedirs(cropping_dir, exist_ok=True)
    os.makedirs(segmented_img_dir, exist_ok=True)

    name_iterator = 1

    for line in json_data["lines"]:

        # Baselines
        baselines = line["baseline"]
        for i in range(1, len(baselines)):
            img = cv.line(img, baselines[i-1],
                          baselines[i], (0, 0, 255), 5)

        # Boundaries
        boundaries = line["boundary"]
        x_min = x_max = boundaries[0][0]
        y_min = y_max = boundaries[0][1]
        for i in range(1, len(boundaries)):
            img = cv.line(img, boundaries[i-1],
                          boundaries[i], (255, 0, 0, 0.25), 5)
            x = boundaries[i][0]
            y = boundaries[i][1]
            x_min = (x if x < x_min else x_min)
            x_max = (x if x > x_max else x_max)
            y_min = (y if y < y_min else y_min)
            y_max = (y if y > y_max else y_max)

        # Crop and save each region segmented by kraken
        if crop:
            if not (os.path.exists(cropped_img_path[:-4]+'_ocr.txt') and os.path.isfile(cropped_img_path[:-4]+'_ocr.txt')):

                cropped = img[y_min:y_max, x_min:x_max].copy()
                cropped_img_path = cropping_dir+os.sep + \
                    filename[:-4]+"_"+str(name_iterator)+".jpg"
                cv.imwrite(cropped_img_path, cropped)

                if predictions:
                    with open(cropped_img_path[:-4]+'_ocr.txt', 'w') as f:
                        f.write(predictions[name_iterator-1].prediction+"\n")
                        # print(predictions[name_iterator-1])
                logger.debug("Created crop :"+cropped_img_path +
                             " with text : "+predictions[name_iterator-1].prediction)

        name_iterator += 1
    cv.imwrite(segmented_img_dir+os.sep+filename[:-4]+"_segmented.jpg", img)


if __name__ == "__main__":

    main_dir = 'test/here'

    process_images(main_dir, ocr=True, crop=False)
