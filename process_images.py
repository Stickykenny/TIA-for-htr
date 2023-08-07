"""
process_image.py: Contains functions for processing images with kraken OCR
"""

from kraken import blla
from kraken import rpred
from kraken.lib import models
from PIL import Image
import cv2 as cv
import os
import pickle
import re
import ujson
import logging
from monitoring import timeit
logger = logging.getLogger("TIA_logger")


# Default model used from https://zenodo.org/record/6657809
# Credits to Chagué, Alix, Clérice, Thibault (2022) HTR-United - Manu McFrench V1 (Manuscripts of Modern and Contemporaneous French)
model_path = 'KrakenModel/HTR-United-Manu_McFrench.mlmodel'
model = models.load_any(model_path)


@timeit
def kraken_segment(im: Image) -> dict:
    """
    Fodder function, to allow @timeit on kraken.blla.segment()

    Parameters :
        im :
            PIL Image object

    Returns :
        Dictionnary produced by kraken.blla.segment()
    """
    return blla.segment(im)


@timeit
def process_images(main_dir: str, crop: bool = False, specific_input: dict = dict()) -> None:
    """
    For all images in a directory, apply segmentation, predictions and cropping

    Parameters :
        main_dir :
            Directory in which images are located
        crop :
            If True, produce all cropped segmentations images in ./cropped/
        specific_input :
            Dictionnary {cote:[images]} indicating which images to process

    Returns :
        None
    """
    # Create output directories
    os.makedirs("tmp"+os.sep+"save"+os.sep+"segment", exist_ok=True)
    os.makedirs("tmp"+os.sep+"save"+os.sep+"ocr_save", exist_ok=True)

    # All available extension, it may differ from what kraken can support
    image_extension = (".jpg", ".png", ".svg", "jpeg")

    # Statistics count
    ocr_count = 0
    segment_count = 0
    nb_img_processed = 0

    for (dirpath, subdirnames, filenames) in os.walk(main_dir):
        for filename in filenames:
            if not filename.lower().endswith(image_extension):
             # skip non-image file
                logger.debug("skipped this non-image file : "+filename)
                continue

            filepath = dirpath+os.sep+filename
            im = Image.open(filepath)

            # Segmentation & Prediction

            predict_backup = "tmp"+os.sep+"save"+os.sep + \
                "ocr_save"+os.sep+filename+'_ocr.pickle'
            segment_save = "tmp"+os.sep+"save"+os.sep + \
                "segment"+os.sep+filename+'_segment.json'

            if os.path.exists(predict_backup) and os.path.isfile(predict_backup):
                # If the ocr result/predict_backup already exists, then there is no need to process the associated image
                continue

            else:
                logger.info("Processing : "+filepath)

                # Segmentation
                if os.path.exists(segment_save) and os.path.isfile(segment_save):
                    # If the segment_save already exists
                    # Load saved result to save time
                    logger.debug(
                        "Loading previous segmentation result "+segment_save)
                    with open(segment_save, 'r', encoding='UTF-8', errors="ignore") as file:
                        baseline_seg = ujson.load(file)
                else:
                    logger.debug("Starting segmentation")
                    baseline_seg = kraken_segment(im)
                    with open(segment_save, 'w', encoding='UTF-8', errors="ignore") as file:
                        ujson.dump(baseline_seg, file, indent=4)
                    segment_count += 1

                # Prediction/OCR
                logger.debug("Starting prediction")
                predictions = ocr_img(model, im, baseline_seg, filename)
                ocr_count += 1

                # Draw segmentation on a copy of the original image
                # and if crop is True, also produce the cropped segmentation
                draw_segmentation(baseline_seg, filepath,
                                  predictions, crop)

            nb_img_processed += 1
            im.close()
            logger.debug("Done with "+str(nb_img_processed)+" images, a total of " + str(segment_count) +
                         " segmentation and " + str(ocr_count) + " ocr were done")


@timeit
def ocr_img(model: models.TorchSeqRecognizer, im: Image, baseline_seg: dict,  filename: str) -> list:
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
        List of Predictions produce by kraken.rpred.rpred()
    """
    ocr_dir = 'tmp'+os.sep+'ocr_result'
    os.makedirs(ocr_dir, exist_ok=True)

    # https://kraken.re/main/api.html#recognition
    predictions = [record for record in rpred.rpred(model, im, baseline_seg)]

    # Backup the ocr_record object to avoid time-consuming steps on relaunch
    with open("tmp"+os.sep+"save"+os.sep+"ocr_save"+os.sep+filename+'_ocr.pickle', 'wb') as file:
        pickle.dump(predictions, file)

    # Also produce a txt file of the result from the prediction
    ocr_filepath = ocr_dir+os.sep+filename[:-4]+'_ocr.txt'
    with open(ocr_filepath, 'w', encoding='UTF-8', errors="ignore") as f:
        for record in predictions:
            f.write(record.prediction+"\n")
        logger.info("Created "+ocr_filepath)

    logger.debug("Saved ocr prediction into "+"tmp"+os.sep +
                 "save"+os.sep+"ocr_save"+os.sep+filename+'_ocr.pickle')

    return predictions


@timeit
def draw_segmentation(json_data: str, filepath: str, predictions: str, crop=False) -> None:
    """
    Draw the segmented region on the image and if crop is True cropped image will be generated at ./cropped/

    Parameters :
        json_data :
            Segmentation data obtained from blla.segment(im)
        filepath :
            The path of the original image
        predictions :
            Prediction produce by kraken.rpred.rpred
        crop :
            If True, it will produce crop result into croppped/

    Returns :
        None
    """

    img = cv.imread(filepath, cv.IMREAD_COLOR)
    filename = filepath.split(os.sep)[-1]

    cropping_dir = "cropped"+os.sep+filename
    segmented_img_dir = "tmp"+os.sep+"segmented"
    os.makedirs(cropping_dir, exist_ok=True)
    os.makedirs(segmented_img_dir, exist_ok=True)

    name_iterator = 1

    # For each segmented part found
    for line in json_data["lines"]:

        """# Draw the baseline of each segmented parts
        baselines = line["baseline"]
        for i in range(1, len(baselines)):
            img = cv.line(img, baselines[i-1],
                          baselines[i], (0, 0, 255), 5)"""

        # Draw the Boundaries of each segmented parts
        boundaries = line["boundary"]
        x_min = x_max = boundaries[0][0]
        y_min = y_max = boundaries[0][1]
        for i in range(1, len(boundaries)):
            img = cv.line(img, boundaries[i-1],
                          boundaries[i], (255, 0, 0, 0.25), 5)
            x = boundaries[i][0]
            y = boundaries[i][1]

            # Take larger coordinates for a rectangle cropping
            x_min = (x if x < x_min else x_min)
            x_max = (x if x > x_max else x_max)
            y_min = (y if y < y_min else y_min)
            y_max = (y if y > y_max else y_max)

        if crop:
            cropped_img_path = cropping_dir+os.sep + \
                filename[:-4]+"_"+str(name_iterator)+".jpg"

            # Crop and save each region segmented by krakens with their associated text as _ocr.txt
            if not (os.path.exists(cropped_img_path[:-4]+'_ocr.txt') and os.path.isfile(cropped_img_path[:-4]+'_ocr.txt')):

                cropped = img[y_min:y_max, x_min:x_max].copy()
                cv.imwrite(cropped_img_path, cropped)

                with open(cropped_img_path[:-4]+'_ocr.txt', 'w', encoding='UTF-8', errors="ignore") as f:
                    f.write(predictions[name_iterator-1].prediction+"\n")
                logger.debug("Created crop :"+cropped_img_path +
                             " with text : "+predictions[name_iterator-1].prediction)

        name_iterator += 1

    # Save the original image with segmentation drawn on it
    cv.imwrite(segmented_img_dir+os.sep+filename[:-4]+"_segmented.jpg", img)


if __name__ == "__main__":

    pass
