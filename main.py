import retrieve_match
import utils_extract
import pdf_text_extract
import os
from time import time
from ast import literal_eval
from shutil import copy as shutilcopy


def retriever(cotes, image_dir, output):
    path = True  # If True, result will show images relative path instead of just the filename

    # Statistics
    total_found = 0
    letters_associated = 0

    # Reset result output
    if os.path.exists(output):
        os.remove(output)

    for dir in next(os.walk(image_dir))[1]:
        path_images_dir = image_dir+os.sep+dir

        images_files = retrieve_match.fetch_images(path_images_dir, path)
        print("For the folder  > "+path_images_dir)
        print("Image count > " + str(len(images_files)) + "| Timer starting now ")
        start_time = time()

        found_matches, cotes_associated = retrieve_match.get_matches(
            cotes, images_files)

        print("Matches found  > " + str(found_matches) +
              " | Time taken : " + str(time() - start_time))

        with open(output, 'a+') as f:
            for i in cotes_associated.items():
                f.write(str(i[0])+":"+str(i[1])+"\n")

        # Statistics
        total_found += found_matches
        letters_associated += len(cotes_associated)
        print("--------------------")
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

    os.makedirs(images_extract_dir, exist_ok=True)
    os.makedirs(pdf_extract_dir, exist_ok=True)
    os.makedirs(txt_extract_dir, exist_ok=True)

    # Retrieve csv data
    autographes = utils_extract.get_column_values(csv_source, column=9)
    cotes = retrieve_match.indexing_autographes(autographes)

    # ---------------

    # Produce in result.txt the association cote:[list_of_images]
    # This one process may take time

    # TODO backup the result to avoid recalculating
    # cotes_associated = retriever(cotes, image_dir, images_links_path)

    cotes_associated = {}
    with open("tmp"+os.sep+"result_images_link_backup.txt") as f:
        for line in f:
            (key, lst) = line.split(":")
            cotes_associated[key] = literal_eval(lst)
    # ---------------

    # Copy images associated to images_extract_dir
    letters_fetched = utils_extract.get_letter_with_n_image(
        images_links_path, 1)
    utils_extract.batch_extract_copy(
        letters_fetched, output_dir=images_extract_dir)

    # Online Fetching PDF, deprecated
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
        new_name = cotes_associated[items[0]][0].split(os.sep)[-1][:-4]+".pdf"
        os.rename(pdf_extract_dir+os.sep +
                  items[1], pdf_extract_dir+os.sep+new_name)

    # Retrieve text from pdf
    pdf_text_extract.retrieve_pdfs_text(
        pdf_extract_dir, output_folder=txt_extract_dir, regroup=False)
