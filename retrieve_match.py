import os
import re
import time
from utils_extract import get_column_values
from hashlib import sha256

image_extension = (".jpg", ".png", ".svg", "jpeg")


def fetch_images(directory: str, path: bool, recursive: bool = True) -> list[str]:
    """
    Retrieve every image file in the directory indicated

    Parameters :
        directory :
            Directory to search images
        path :
            If True, images will be fetched with their relative path instead of their filename
        recursive :
            If True, the search will also go into subdirectory

    Return :
        List of all images fetched in the given directory
    """
    images_files = []
    for (dirpath, subdirnames, filenames) in os.walk(directory):
        if path:
            images_files.extend(
                [dirpath+os.sep+f for f in filenames if f.lower().endswith(image_extension)])
        else:
            images_files.extend(
                [f for f in filenames if f.lower().endswith(image_extension)])
        if not recursive:
            break
    return images_files


def indexing_autographes(autographes: list[str]):
    """
    Retrieve into a dictionnary the association cote->autographe from a list of autographes
    This function is highly fitted for naming convention of "MsXXX-X.. .jpg"

    Parameters :
        autographes :
            List of autographes

    Return :
        Dictionnary associating cote->autographe
    """
    cotes = {}
    for letter_name in autographes:
        # print(letter_name, end=" | ")
        cote = ""
        for numbers in re.findall(r"(\d+(?:-\d+)*(?:bis+)*(?: bis+)*(?:ter+)*(?: ter+)*)", letter_name):
            # Concatenate every cotes from the same letter with "+" sign
            if cote != "":
                cote += "+"
            cote += numbers
        cote = cote.replace(" ", "")
        if cote != "":
            cotes[cote] = letter_name
            # print(cote +"  ->  "+ letter_name)
    return cotes


def get_matches(cotes: dict, images_files: list[str]) -> tuple[int, dict]:
    """
    Associate every cotes their images if it exists

    Parameters :
        cotes :
            Dictionnary of cotes
        images_files :
            List containing paths to images

    Return :
        Number of matches found, Dictionnary of available cotes with images
    """
    count = 0
    cotes_availables = {}

    files = sorted([i for i in images_files if i.split(
        os.sep)[-1].lower().startswith("ms")])
    current_size = len(files)
    i = 0
    # To find matches more efficiently, we remove images found associated
    # This can be optimized probably
    while i < current_size:
        cotes, count, cotes_availables, files, current_size, i = __compare_match(
            cotes, count, cotes_availables, files, current_size, i)
    return count, cotes_availables


def __compare_match(cotes, count, cotes_availables, files, current_size, i):
    """
    Private function used to loop though every cote, it was created because 'break' couldn't break out of outer loop
    """
    for cote_group in cotes.keys():
        # Loop though each cote_group (some letter have 2 cotes)
        for cote in cote_group.split("+"):

            # Normalize cote from the file to fit the csv
            filename = files[i].lower()
            # print(filename)
            for cote_in_name in re.findall(r"(\d+(?:-\d+)*(?:bis+)*(?: bis+)*(?:ter+)*(?: ter+)*)", filename):
                # print(filename+">> "+cote_in_name + " ==? "+ cote )
                if cote == cote_in_name.replace(" ", ""):

                    if cote not in cotes_availables:
                        cotes_availables[cote] = []
                    cotes_availables[cote].append(files[i])
                    count += 1
                    # Optimize by removing image already associated
                    del files[i]
                    current_size -= 1
                    return cotes, count, cotes_availables, files, current_size, 0
    else:
        return cotes, count, cotes_availables, files, current_size, i+1


if __name__ == "__main__":

    # Dictionnaire
    # cotes : [ code : nom complet de l'autographe ]
    # cotes_available : [ code : [ liste des noms de fichiers images ]]

    path = False  # If True, result will show images relative path instead of just the filename

    # Retrieve csv data
    csv_source = 'Correspondance MDV - Site https __www.correspondancedesbordesvalmore.com - lettres.csv'
    autographes = get_column_values(csv_source, column=9)

    # Statistics
    total_found = 0
    letters_associated = 0

    # Filename of the save will be based on a hash made on result of os.walk('Images')
    hash_filename = sha256(
        str([i for i in os.walk("Images")]).encode('utf-8')).hexdigest()
    result_filepath = "tmp"+os.sep+"save" + \
        os.sep+"match" + str(hash_filename)+".txt"
    # Reset result output
    if os.path.exists(result_filepath):
        os.remove(result_filepath)

    for dir in next(os.walk('Images'))[1]:
        path_images_dir = "Images"+os.sep+dir

        images_files = fetch_images(path_images_dir, path)
        print("For the folder  > "+path_images_dir)
        print("Image count > " + str(len(images_files)) + "| Timer starting now ")
        start_time = time.time()

        cotes = indexing_autographes(autographes)
        found_matches, cotes_associated = get_matches(cotes, images_files)

        print("Matches found  > " + str(found_matches) +
              " | Time taken : " + str(time.time() - start_time))

        with open(result_filepath, 'a+') as f:
            for i in cotes_associated.items():
                f.write(str(i[0])+":"+str(i[1])+"\n")

        # Statistics
        total_found += found_matches
        letters_associated += len(cotes_associated)
        print("--------------------")
    print("Found in total "+str(total_found)+" matches of images with letter\nTotalling " +
          str(letters_associated)+" letters associated")
