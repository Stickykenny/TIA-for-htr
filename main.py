import retrieve_match
import utils_extract
import pdf_text_extract
import os
from time import time
from ast import literal_eval as ast_literal_eval
from shutil import copy as shutilcopy
import pickle
from hashlib import sha256


def retriever(cotes, image_dir, output):
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
        print("For the folder  > "+path_images_dir)
        print("Image count > " + str(len(images_files)) + "| Timer starting now ")
        start_time = time()

        found_matches, cotes_associated_part = retrieve_match.get_matches(
            cotes, images_files)
        cotes_associated |= cotes_associated_part

        print("Matches found  > " + str(found_matches) +
              " | Time taken : " + str(time() - start_time))

        # Statistics
        total_found += found_matches
        letters_associated += len(cotes_associated_part)
        print("--------------------")

        # Make a save of matches understandable by humans
        last_saved = "tmp"+os.sep+"save"+os.sep+"last_matches.txt"
        with open(last_saved, 'a+') as f:
            for i in cotes_associated_part.items():
                f.write(str(i[0])+":"+str(i[1])+"\n")

    print("\tSaved matches here "+last_saved)

    # Save the dictionnary object with pickle
    with open(result_filepath, 'ab+') as file:
        pickle.dump(cotes_associated, file)
    print("\tSaved backup dictionnary of matches here : "+result_filepath)

    print("Found in total "+str(total_found)+" matches of images with letter\nTotalling " +
          str(letters_associated)+" letters associated")
    return cotes_associated


if __name__ == "__main__":
    csv_source = 'Correspondance MDV - Site https __www.correspondancedesbordesvalmore.com - lettres.csv'
    pdf_source = 'MDV-site-Xavier-Lang'
    image_dir = 'Images'
    images_links_path = "tmp"+os.sep+"result_images_link.txt"
    images_extract_dir = "tmp"+os.sep+"extract_image"
    pdf_extract_dir = "tmp"+os.sep+"extract_pdf"
    txt_extract_dir = "tmp"+os.sep+"extract_txt"

    # Filename of the save of matches will be based on a hash made on result of os.walk('Images')
    hash_filename = sha256(
        str([i for i in os.walk("Images")]).encode('utf-8')).hexdigest()
    result_filepath = "tmp"+os.sep+"save"+os.sep+"match"+os.sep + \
        str(hash_filename)+".pickle"

    os.makedirs(images_extract_dir, exist_ok=True)
    os.makedirs(pdf_extract_dir, exist_ok=True)
    os.makedirs(txt_extract_dir, exist_ok=True)

    os.makedirs("tmp"+os.sep+"save"+os.sep+"match", exist_ok=True)

    # Retrieve csv data
    autographes = utils_extract.get_column_values(csv_source, column=9)
    cotes = retrieve_match.indexing_autographes(autographes)

    # ---------------

    cotes_associated = {}
    """
    # Old backup system
    if os.path.exists("tmp"+os.sep+"result_images_link_backup.txt"):

        with open("tmp"+os.sep+"result_images_link_backup.txt") as f:
            for line in f:
                (key, lst) = line.split(":")
                cotes_associated[key] = ast_literal_eval(lst)
    else :
        # Produce in result.txt the association cote:[list_of_images]
        # This one process may take time

        cotes_associated = retriever(cotes, image_dir, result_filepath)
    """
    if (os.path.exists(result_filepath) and os.path.isfile(result_filepath)):
        # Load saved result to save time
        with open(result_filepath, 'rb') as file:
            cotes_associated = pickle.load(file)
        print("\tLoaded matches from last result from "+result_filepath)
    else:
        # This one process may take time
        cotes_associated = retriever(cotes, image_dir, result_filepath)

    # ---------------

    # Copy images associated to images_extract_dir
    letters_fetched = utils_extract.get_letter_with_n_image(
        images_links_path, 1)
    utils_extract.batch_extract_copy(
        letters_fetched, output_dir=images_extract_dir)

    # Online Fetching PDF, DEPRECATED METHOD
    """
    # Download necessary pdf
    print("extract link")
    links = utils_extract.extract_column_from_csv(csv_source, c1=3, c2=9,
                                                  list_to_compare=list(letters_fetched.keys()))
    utils_extract.batch_download_pdf_gdrive(
        links, output_dir="tmp/extract_pdf", name_associated=cotes_associated)

    """

    pdfs_matched_repo = sorted(list(utils_extract.extract_column_from_csv(csv_source, c1=4, c2=9,
                                                                          list_to_compare=list(letters_fetched.keys())).items()), key=lambda x: x[0])

    # Retrieve pdf and rename them to fit image files' name
    for items in pdfs_matched_repo:
        shutilcopy(pdf_source+os.sep+items[1], pdf_extract_dir)
        # new_name = cotes_associated[items[0]][0].split(os.sep)[-1][:-4]+".pdf"
        new_name = items[0]+".pdf"  # Using cote as txt file name

        os.rename(pdf_extract_dir+os.sep +
                  items[1], pdf_extract_dir+os.sep+new_name)

    # Retrieve text from pdf
    pdf_text_extract.retrieve_pdfs_text(
        pdf_extract_dir, output_folder=txt_extract_dir, regroup=False)
