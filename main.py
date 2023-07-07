import retrieve_match
import utils_extract
import pdf_text_extract
import os
from time import time


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
    image_dir = 'Images'
    images_links_path = "tmp"+os.sep+"result_images_link.txt"

    # Retrieve csv data
    autographes = utils_extract.get_column_values(csv_source, column=9)
    cotes = retrieve_match.indexing_autographes(autographes)

    # Produce in result.txt the association cote:[list_of_images]
    # This one process may take time

    cotes_associated = retriever(cotes, image_dir, images_links_path)

    # Copy images associated to images_extract_dir
    images_extract_dir = "tmp"+os.sep+"images_extract"
    letters_fetched = utils_extract.get_letter_with_n_image(
        images_links_path, 1)
    utils_extract.batch_extract_copy(
        letters_fetched, output_dir=images_extract_dir)

    print("extract link")
    links = utils_extract.extract_filelink_from_drive(csv_source, c1=3, c2=9,
                                                      list_to_compare=list(letters_fetched.keys()))
    utils_extract.batch_download_pdf_gdrive(
        links, output_dir="tmp/extract_pdf")
