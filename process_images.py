"""
process_image.py: Contains functions for processing images with kraken OCR
"""

from kraken import blla
from kraken import rpred
from kraken.lib import models
from kraken import serialization
from PIL import Image
import os
import pickle
import ujson
import logging
from monitoring import timeit
logger = logging.getLogger("TIA_logger")


# Default model used from https://zenodo.org/record/6657809
# Credits to Chagué, Alix, Clérice, Thibault (2022) HTR-United - Manu McFrench V1 (Manuscripts of Modern and Contemporaneous French)
model_path = 'models'+os.sep+'HTR-United-Manu_McFrench.mlmodel'
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
def serialize_alto(image_filepath: str, predictions: list) -> str:
    """
    Serialize the result of the ocr prediction by Kraken

    Parameters :
        image_filepath :
            Path to the image file
        predictions :
            List of ocr_record produced by Kraken's OCR

    Returns :
        Text content of the ALTO produced
    """
    im = Image.open(image_filepath)
    alto = serialization.serialize(
        predictions, image_name=image_filepath.split(os.sep)[-1], image_size=im.size, template="alto")
    im.close()
    return alto


@timeit
def process_images(main_dir: str) -> None:
    """
    For all images in a directory, apply segmentation and prediction

    Parameters :
        main_dir :
            Directory in which images are located

    Returns :
        None
    """
    # Create output directories
    os.makedirs("tmp"+os.sep+"save"+os.sep+"segment", exist_ok=True)
    os.makedirs("tmp"+os.sep+"save"+os.sep+"ocr_save", exist_ok=True)
    os.makedirs("tmp"+os.sep+"save"+os.sep+"ocr_serialized", exist_ok=True)

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

            # Path to the saved data
            predict_backup = "tmp"+os.sep+"save"+os.sep + \
                "ocr_save"+os.sep+filename+'_ocr.pickle'
            segment_save = "tmp"+os.sep+"save"+os.sep + \
                "segment"+os.sep+filename+'_segment.json'
            alto_xml_save = "tmp"+os.sep+"save"+os.sep + \
                "ocr_serialized"+os.sep+filename+'_ocr.xml'

            if os.path.exists(predict_backup) and os.path.isfile(predict_backup):
                # If the ocr result/predict_backup already exists, then there is no need to process the associated image
                if not os.path.exists(alto_xml_save):
                    with open(predict_backup, 'rb') as file:
                        predictions = pickle.load(file)

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

            # ALTO XML, predictions serialized format
            if not os.path.exists(alto_xml_save):
                logger.debug("Starting Serialization")
                alto = serialize_alto(filepath, predictions)
                with open(alto_xml_save, 'w', encoding="UTF-8", errors="ignore") as fp:
                    fp.write(alto)

            nb_img_processed += 1
            im.close()
            logger.debug("Done with "+filename+", "+str(nb_img_processed)+" images, a total of " + str(segment_count) +
                         " segmentation and " + str(ocr_count) + " ocr were done")
