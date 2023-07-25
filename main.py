"""

usage : main.py [set_number]

set_number : Specify the group to be processed, with n the number of image per autographe
"""

import sys
import retrieve_match
import utils_extract
import pdf_text_extract
import process_images
import align
import os
from time import time
from shutil import copy as shutilcopy
import pickle
from hashlib import sha256
import monitoring
import logging
logger = logging.getLogger("align_logger")


def retriever(cotes: dict, image_dir: str, output: str) -> dict:
    """
    Retrieve informations to create the dictionnary {cote:[images]}

    Parameters :
        cotes :
            Directory to search images, {cote:autographe}
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
    for dir in next(os.walk(image_dir))[1]:
        path_images_dir = image_dir+os.sep+dir

        # List all images in current directory
        images_files = retrieve_match.fetch_images(path_images_dir, path)

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
    with open(last_saved, 'w') as f:
        for i in cotes_associated_part.items():
            f.write(str(i[0])+":"+str(i[1])+"\n")

    logger.info("\tSaved matches here "+last_saved)

    # Save the dictionnary object with pickle
    with open(result_filepath, 'ab+') as file:
        pickle.dump(cotes_associated, file)

    logger.info("\tSaved backup dictionnary of matches here : "+result_filepath)

    logger.info("Found in total "+str(total_found)+" matches of images with letter\nTotalling " +
                str(letters_associated)+" letters associated")
    return cotes_associated


def processing_pdfs(pdf_source: str, csv_source: str, letters_fetched: dict, pdf_extract_dir: str = "tmp"+os.sep+"extract_pdf", c1: int = 4, c2: int = 9) -> None:
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
        pdf_extract_dir, output_folder=txt_extract_dir, regroup=False)


if __name__ == "__main__":

    # Indicate in CLI which cote you want to process by number of images associated
    # Default is -1, meaning every cote is processed
    if len(sys.argv) > 1:
        if sys.argv[1].isdigit():
            nb_image_check = int(sys.argv[1])
    else:
        nb_image_check = -1

    # Logger
    logger = monitoring.setup_logger()

    # Define files and directory location
    csv_source = 'Correspondance MDV - Site https __www.correspondancedesbordesvalmore.com - lettres.csv'
    pdf_source = 'MDV-site-Xavier-Lang'
    image_dir = 'Images'
    images_extract_dir = "tmp"+os.sep+"extract_image"
    txt_extract_dir = "tmp"+os.sep+"extract_txt"

    # Filename of the save of matches will be based on a hash made on result of os.walk('Images')
    hash_filename = sha256(
        str([i for i in os.walk("Images")]).encode('utf-8')).hexdigest()
    result_filepath = "tmp"+os.sep+"save"+os.sep+"match"+os.sep + \
        str(hash_filename)+".pickle"

    # Create directories for save and results
    os.makedirs(images_extract_dir, exist_ok=True)
    os.makedirs(txt_extract_dir, exist_ok=True)
    os.makedirs("tmp"+os.sep+"save"+os.sep+"match", exist_ok=True)

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
        cotes_associated = retriever(cotes, image_dir, result_filepath)

    # -------------------------------------------------------------------

    # Copy images associated to images_extract_dir
    if nb_image_check <= 0:
        logger.info("Fetching all matches of letter with images")
    else:
        logger.info("Fetching all matches of letter with " +
                    str(nb_image_check) + " image(s)")

    # -------------------------------------------------------------------

    # Filter out some cote
    letters_fetched = utils_extract.get_letter_with_n_image(
        result_filepath, nb_image_check, cotes_associated)
    if len(letters_fetched) == 0:
        logger.info("No letter found, exiting program")
        sys.exit()

    utils_extract.batch_extract_copy(
        letters_fetched, output_dir=images_extract_dir)

    # PDF Processing
    logger.info("Retrieving pdfs' content")
    processing_pdfs(pdf_source, csv_source, letters_fetched,
                    pdf_extract_dir="tmp"+os.sep+"extract_pdf")

    # -------------------------------------------------------------------

    # Process images (segment, predict, crop)
    logger.info("Processing images")
    process_images.process_images(
        images_extract_dir, crop=False, specific_input=letters_fetched)

    # -------------------------------------------------------------------

    # Alignment text-image of cropped part of an image
    align.batch_align_crop(images_extract_dir, specific_input=letters_fetched)
