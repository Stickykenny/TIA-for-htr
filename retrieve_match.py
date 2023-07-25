"""
retrieve_match.py: Contains functions for the task of fetching the usable data
"""

import os
import re
import logging
logger = logging.getLogger("align_logger")

image_extension = (".jpg", ".png", ".svg", "jpeg")


def fetch_images(directory: str, path: bool, recursive: bool = True) -> list:
    """
    Retrieve every image file in the directory indicated

    Parameters :
        directory :
            Directory to search images
        path :
            If True, images will be fetched with their relative path instead of their filename
        recursive :
            If True, the search will also go into subdirectory

    Returns :
        List of all images fetched in the given directory
    """
    images_files = []
    for (dirpath, subdirnames, filenames) in os.walk(directory):

        if path:
            # if True, retrieve images' filepath instead of filename
            images_files.extend(
                [dirpath+os.sep+f for f in filenames if f.lower().endswith(image_extension)])
        else:
            images_files.extend(
                [f for f in filenames if f.lower().endswith(image_extension)])

        if not recursive:
            break

    logger.debug("Found "+str(len(images_files))+" images inside " +
                 directory + " recurssively" if recursive else "without recursion")
    return images_files


def indexing_autographes(autographes: list) -> dict:
    """
    Retrieve into a dictionnary the association cote->autographe from a list of autographes
    This function is highly fitted for naming convention of "MsXXX-X.. .jpg"

    Parameters :
        autographes :
            List of autographes

    Returns :
        Dictionnary associating cote->autographe
    """
    cotes = {}
    for letter_name in autographes:
        cote = ""

        # Regex expression to get only cote from file name, it also takes into account
        # "bis" et "ter" denomination with the convention XXXX-XXX-XX

        for numbers in re.findall(r"(\d+(?:-\d+)+(?:bis+)*(?: bis+)*(?:ter+)*(?: ter+)*)", letter_name):
            # Concatenate every cotes from the same letter with "+" sign
            if cote != "":
                cote += "+"
            cote += numbers
        cote = cote.replace(" ", "")
        if cote != "":
            cotes[cote] = letter_name
    return cotes


def get_matches(cotes: dict, images_files: list) -> tuple:
    """
    Associate every cotes their images if it exists

    Parameters :
        cotes :
            Dictionnary of {cotecote:autographe}
        images_files :
            List containing paths to images

    Returns :
        Number of matches found, Dictionnary of available cotes with images
    """
    count = 0
    cotes_availables = {}

    # In a sorted list, we fetch filename
    files = sorted([i for i in images_files if i.split(
        os.sep)[-1].lower().startswith("ms")])
    current_size = len(files)
    i = 0

    # To find matches more efficiently, we remove images found associated
    # This can be optimized probably

    # This algorithm works by iterating with i through every files
    while i < current_size:
        cotes, count, cotes_availables, files, current_size, i = __compare_match(
            cotes, count, cotes_availables, files, current_size, i)

    return count, cotes_availables


def __compare_match(cotes, count, cotes_availables, files, current_size, i):
    """
    Private function used to loop though every cote, it was created because 'break' couldn't break out of outer loop
    ( see get_matches() )
    """
    for cote_group in cotes.keys():
        # Loop though each cote_group (some letter have 2 cotes)
        for cote in cote_group.split("+"):

            # Normalize cote from the file to fit the csv
            # Same regex as in indexing_autographes()

            filename = files[i].lower()
            for cote_in_name in re.findall(r"(\d+(?:-\d+)+(?:bis+)*(?: bis+)*(?:ter+)*(?: ter+)*)", filename):
                if cote == cote_in_name.replace(" ", ""):

                    # Init a list for new entry
                    if cote not in cotes_availables:
                        cotes_availables[cote] = []

                    # Append to this list every
                    cotes_availables[cote].append(files[i])
                    count += 1

                    # Optimize by removing image already associated
                    logger.debug("Matched "+str(count) + " image(s)")
                    del files[i]
                    current_size -= 1

                    return cotes, count, cotes_availables, files, current_size, 0
    else:
        return cotes, count, cotes_availables, files, current_size, i+1


if __name__ == "__main__":

    # Dictionnaire
    # cotes : [ code : nom complet de l'autographe ]
    # cotes_available : [ code : [ liste des noms de fichiers images ]]
    pass
