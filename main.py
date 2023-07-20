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
from ast import literal_eval as ast_literal_eval
from shutil import copy as shutilcopy
import pickle
from hashlib import sha256
import monitoring
import logging
logger = logging.getLogger("align_logger")


def retriever(cotes: dict[str, str], image_dir: str, output: str) -> dict:

    path = True  # If True, result will show images relative path instead of just the filename

    # Statistics
    total_found = 0
    letters_associated = 0

    # Reset result output
    if os.path.exists(output):
        os.remove(output)
    cotes_associated = dict()
    for dir in next(os.walk(image_dir))[1]:
        path_images_dir = image_dir+os.sep+dir

        images_files = retrieve_match.fetch_images(path_images_dir, path)
        logger.info("For the folder  > "+path_images_dir)
        logger.info("Image count > " + str(len(images_files)) +
                    "| Timer starting now ")
        start_time = time()

        found_matches, cotes_associated_part = retrieve_match.get_matches(
            cotes, images_files)
        cotes_associated |= cotes_associated_part

        logger.info("Matches found  > " + str(found_matches) +
                    " | Time taken : " + str(time() - start_time))

        # Statistics
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


def processing_pdfs(pdf_source: str, csv_source: str, letters_fetched: dict, pdf_extract_dir: str = "tmp"+os.sep+"extract_pdf") -> None:

    os.makedirs(pdf_extract_dir, exist_ok=True)
    pdfs_matched_repo = sorted(list(utils_extract.extract_column_from_csv(csv_source, c1=4, c2=9,
                                                                          list_to_compare=list(letters_fetched.keys())).items()), key=lambda x: x[0])

    # Retrieve pdf and rename them to fit image files' name*
    for items in pdfs_matched_repo:
        shutilcopy(pdf_source+os.sep+items[1], pdf_extract_dir)
        # new_name = cotes_associated[items[0]][0].split(os.sep)[-1][:-4]+".pdf"
        new_name = items[0]+".pdf"  # Using cote as txt file name

        os.rename(pdf_extract_dir+os.sep +
                  items[1], pdf_extract_dir+os.sep+new_name)

    # Retrieve text from pdf
    pdf_text_extract.retrieve_pdfs_text(
        pdf_extract_dir, output_folder=txt_extract_dir, regroup=False)


if __name__ == "__main__":

    if len(sys.argv) > 1:
        if sys.argv[1].isdigit():
            nb_image_check = int(sys.argv[1])
    else:
        nb_image_check = -1

    # Loggers
    logger = monitoring.setup_logger()

    csv_source = 'Correspondance MDV - Site https __www.correspondancedesbordesvalmore.com - lettres.csv'
    pdf_source = 'MDV-site-Xavier-Lang'
    image_dir = 'Images'
    images_links_path = "tmp"+os.sep+"result_images_link.txt"
    images_extract_dir = "tmp"+os.sep+"extract_image"
    txt_extract_dir = "tmp"+os.sep+"extract_txt"

    # Filename of the save of matches will be based on a hash made on result of os.walk('Images')
    hash_filename = sha256(
        str([i for i in os.walk("Images")]).encode('utf-8')).hexdigest()
    result_filepath = "tmp"+os.sep+"save"+os.sep+"match"+os.sep + \
        str(hash_filename)+".pickle"

    os.makedirs(images_extract_dir, exist_ok=True)
    os.makedirs(txt_extract_dir, exist_ok=True)
    os.makedirs("tmp"+os.sep+"save"+os.sep+"match", exist_ok=True)

    # Retrieve csv data
    autographes = utils_extract.get_column_values(csv_source, column=9)
    cotes = retrieve_match.indexing_autographes(autographes)
    logger.debug("Retrieved csv data")
    # ---------------

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

    # Copy images associated to images_extract_dir
    if nb_image_check <= 0:
        logger.info("Fetching all matches of letter with images")
    else:
        logger.info("Fetching all matches of letter with " +
                    str(nb_image_check) + " image(s)")
    letters_fetched = utils_extract.get_letter_with_n_image(
        images_links_path, nb_image_check)

    if len(letters_fetched) == 0:
        logger.info("No letter found, exiting program")
        sys.exit()

    utils_extract.batch_extract_copy(
        letters_fetched, output_dir=images_extract_dir)

    # PDF Processing
    logger.info("Retrieving pdfs' content")
    processing_pdfs(pdf_source, csv_source, letters_fetched,
                    pdf_extract_dir="tmp"+os.sep+"extract_pdf")

    # Process images (segment, predict, crop)
    logger.info("Processing images")
    process_images.process_images(
        images_extract_dir, crop=False, specific_input=letters_fetched)

    # Alignment text-image of cropped part of an image
    align.batch_align_crop(images_extract_dir, specific_input=letters_fetched)
