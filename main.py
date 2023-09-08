"""
usage : main.py
"""

import logging
import monitoring
from hashlib import sha256
import pickle
from shutil import copy as shutilcopy
from time import time
from monitoring import timeit
import os
import re
import align
import process_images
import sys
import retrieve_match
import utils_extract
import preprocess_image
import pdf_text_extract
import add_align

logger = logging.getLogger("TIA_logger")


def retriever(cotes: dict, image_dir: str, output: str, result_filepath: str) -> dict:
    """
    Retrieve informations to create the dictionnary {cote:[images]}

    Parameters :
        cotes :
            Dictionnary associating cote->autographe
        image_dir :
            Directory to search images,
        result_filepath :
            Path to dump list of all images fetched
        path :
            If True, images will be fetched with their relative path instead of their filename
        recursive :
            If True, the search will also go into subdirectory

    Returns :
        List of all images fetched in the given directory
    """
    path = True  # If True, result will show images relative path instead of just the filename

    # Statistics
    total_found = 0
    letters_associated = 0

    # Reset result output
    if os.path.exists(output):
        os.remove(output)
    cotes_associated = dict()

    # For each folder inside
    for directory, subfolder, files in os.walk(image_dir):
        path_images_dir = directory
        # List all images in current directory
        images_files = retrieve_match.fetch_images(
            path_images_dir, path, recursive=False)

        # Logs & Statistics
        logger.info("For the folder  > "+path_images_dir)
        logger.info("Image count > " + str(len(images_files)) +
                    "| Timer starting now ")
        start_time = time()

        found_matches, cotes_associated_part = retrieve_match.get_matches(
            cotes, images_files)

        # Append retrieved dictionnary of cotes into the main dictionnary
        # cotes_associated |= cotes_associated_part #
        for e in cotes_associated_part:
            if e not in cotes_associated:
                cotes_associated[e] = cotes_associated_part[e]

        # Logs the number of images found and the time taken to find them
        logger.info("Matches found  > " + str(found_matches) +
                    " | Time taken : " + str(time() - start_time))

        # Statistics count
        total_found += found_matches
        letters_associated += len(cotes_associated_part)

    # Make a save of matches understandable by humans
    last_saved = "tmp"+os.sep+"save"+os.sep+"last_matches.txt"
    with open(last_saved, 'w', encoding='UTF-8', errors="ignore") as f:
        for i in cotes_associated.items():
            f.write(str(i[0])+":"+str(i[1])+"\n")

    logger.info("\tSaved matches here "+last_saved)

    # Save the dictionnary object with pickle
    with open(result_filepath, 'ab+') as file:
        pickle.dump(cotes_associated, file)

    logger.info("\tSaved backup dictionnary of matches here : "+result_filepath)

    logger.info("Found in total "+str(total_found)+" matches of images with letter\nTotalling " +
                str(letters_associated)+" letters associated")
    return cotes_associated


@timeit
def processing_pdfs(pdf_source: str, csv_source: str, letters_fetched: dict, pdf_extract_dir: str = "tmp"+os.sep+"extract_pdf", txt_extract_dir: str = "tmp"+os.sep+"extract_txt", c1: int = 4, c2: int = 9) -> None:
    """
    For all letters specified in letters_fetched, extract the text of the pdf associated into pdf_extract_dir if present in pdf_source

    Parameters :
        pdf_source :
            Path of the folder where all the pdfs are located
        csv_source :
            Path of the csv file containig the information for association
        letters_fetched :
            Dictionnary containing in his keys all cotes available
        pdf_extract_dir :
            Directory where the pdf will be extracted to
        c1 :
            Index of the column in the csv where values are
            (Default value is tailored for MDV)
        c2 :
            Index of the column in the csv where cotes to compare are
            (Default value is tailored for MDV)

    Returns :
        None
    """
    os.makedirs(pdf_extract_dir, exist_ok=True)

    # Retrieve into a sorted list all pdfs usable
    pdfs_matched_repo = sorted(list(utils_extract.extract_column_from_csv(csv_source, c1=4, c2=9,
                                                                          list_to_compare=list(letters_fetched.keys())).items()), key=lambda x: x[0])

    # Copy pdf into pdf_extract_dir and rename them to fit "{cote}.pdf"
    for items in pdfs_matched_repo:
        shutilcopy(pdf_source+os.sep+items[1], pdf_extract_dir)
        new_name = items[0]+".pdf"  # Using cote as txt file name

        os.rename(pdf_extract_dir+os.sep +
                  items[1], pdf_extract_dir+os.sep+new_name)

    # For all pdf in pdf_extract_dir, extract the text into a file name "{cote.gt.txt}" (.gt.txt is the sufix used in kraken/ketos)
    pdf_text_extract.retrieve_pdfs_text(
        pdf_extract_dir, output_folder=txt_extract_dir, syllabification_cut=True)

    # Now duplicate transcription for each images, rename them for each image their own transcription file
    # It will for each image, find the associated transcriptions, then duplicate it with the image filename
    destination_folder = "tmp"+os.sep+"extract_txt"+os.sep
    for dirpath, subfolders, files in os.walk("tmp"+os.sep+"extract_image"):
        for image in files:
            if image.endswith((".jpg", ".png")):
                image_cote = re.search(
                    r"(\d+(?:-\d+)+(?:bis+)*(?: bis+)*(?:ter+)*(?: ter+)*)", image).group(1)
                cote_file = image_cote+".gt.txt"
                try:
                    shutilcopy(destination_folder+cote_file,
                               destination_folder+image[:-4]+".gt.txt")
                except:
                    logger.info("Error Copying "+cote_file)

        break


def prepare_data(images_extract_dir: str, txt_extract_dir: str) -> dict:
    """
    Process to retrieve only images with transcription (for the MDV dataset)

    Parameters :
        images_extract_dir :
            Directory to where images will be extracted to
        txt_extract_dir :
            Directory to where transcriptions will be extracted to

    Returns :
        Dictionary of all letters fetched : associating cote->images_list
    """
    image_dir = 'images'
    csv_source = 'Correspondance MDV - Site https __www.correspondancedesbordesvalmore.com - lettres.csv'
    pdf_source = 'MDV-site-Xavier-Lang'

    # Filename of the save of matches will be based on a hash made on result of os.walk('images')
    hash_filename = sha256(
        str([i for i in os.walk("images")]).encode('utf-8')).hexdigest()
    result_filepath = "tmp"+os.sep+"save"+os.sep+"match"+os.sep + \
        str(hash_filename)+".pickle"

    # Retrieve from csv every cote in the form of a dictionnary cote:autographe
    autographes = utils_extract.get_column_values(csv_source, column=9)
    cotes = retrieve_match.indexing_autographes(autographes)
    logger.debug("Retrieved csv data")

    # -------------------------------------------------------------------

    # Find images associated with cotes
    cotes_associated = {}
    if (os.path.exists(result_filepath) and os.path.isfile(result_filepath)):
        # Load saved result to save time
        with open(result_filepath, 'rb') as file:
            cotes_associated = pickle.load(file)
        logger.info(
            "Loaded matches from previous result from "+result_filepath)
    else:
        # This one process may take time
        cotes_associated = retriever(
            cotes, image_dir, result_filepath, result_filepath)

    # -------------------------------------------------------------------

    # Copy images associated to images_extract_dir
    logger.info("Fetching all matches of letter with images")
    letters_fetched = utils_extract.get_letter_with_n_image(
        result_filepath, -1, cotes_associated)
    if len(letters_fetched) == 0:
        logger.info("No letter found, exiting program")
        sys.exit()

    utils_extract.batch_extract_copy(
        letters_fetched, output_dir=images_extract_dir)

    # -------------------------------------------------------------------

    # PDF Processing
    logger.info("Retrieving pdfs' content")
    processing_pdfs(pdf_source, csv_source, letters_fetched=letters_fetched,
                    pdf_extract_dir="tmp"+os.sep+"extract_pdf", txt_extract_dir=txt_extract_dir)

    return letters_fetched


if __name__ == "__main__":

    # Logger
    logger = monitoring.setup_logger()

    # Define files and directory location
    image_dir = 'images'
    images_extract_dir = "tmp"+os.sep+"extract_image"
    txt_extract_dir = "tmp"+os.sep+"extract_txt"

    # Create directories for save and results
    os.makedirs(images_extract_dir, exist_ok=True)
    os.makedirs(txt_extract_dir, exist_ok=True)
    os.makedirs("tmp"+os.sep+"save"+os.sep+"match", exist_ok=True)

    # -------------------------------------------------------------------
    logger.info("Pre-processing images ...")
    # Pre-process image files

    # Split double pages into 2 single pages
    # preprocess_image.batch_preprocess(images_extract_dir)

    # ----------------------------------------------------
    # DATA PREPARATION for the MDV dataset ----------------

    # prepare_data(images_extract_dir, txt_extract_dir)

    # End of DATA PREPARATION ----------------
    # ----------------------------------------------------

    # Process images (segment, predict, crop)

    logger.info("Processing images")
    process_images.process_images(images_extract_dir)

    # -------------------------------------------------------------------

    # Alignment text-image of cropped part of an image
    align.batch_align_crop(images_extract_dir, printing=True)

    # Statistics
    logger.info("Starting statistics calculations")
    monitoring.generate_compare_html("tmp"+os.sep+"cropped_match")
    monitoring.quantify_segment_used(
        images_extract_dir, "tmp"+os.sep+"cropped_match", 'tmp'+os.sep+'save'+os.sep+'segment')
    logger.info("Finished statistics calculations")

    # Using statistics, provide a manual way to align the worst page aligned
    logger.info(
        "You can use add_align.py to manually add alignments, the 10 first worst page have been generated in manual_align/")
    add_align.generate_manual_alignments(10)

    print(add_align.__doc__)
