"""
utils_extract.py: Contains functions related to extracting informations/data
"""
from monitoring import timeit
import os
from shutil import copy, move
import csv
import logging
import pickle
import sys
logger = logging.getLogger("TIA_logger")


def get_column_values(csv_source: str, column: int = 9) -> list:
    """

    Retrieve into a list all values from the n column

    Parameters :
        csv_source :
            The path of the csv file
        column :
            Index of the column to be extracted

    Returns :
        List of all values in selected column in the csv file
    """
    with open(csv_source, newline='', encoding='UTF-8', errors="ignore") as inputfile:
        return [row[column] for row in csv.reader(inputfile) if row[column] != ""]


def get_letter_with_n_image(file: str, n: int = -1, loaded: dict = dict()) -> dict:
    """
    Retrieve all letters' cote having only n image
    if n = -1, this function will simply convert the file into a python dictionnary

    Parameters :
        file :
            The path of the file containing a dict
        n :
            The sound the animal makes
        loaded :
            The dictionnary of {cote:[images]}, overwrite the file parameter

    Returns :
        The dictionnary {cote:[images]} of every letter having n images
    """
    letters_fetched = dict()
    count = 0
    if not loaded:
        # If no dictionnary was used, load from the saved pickle
        with open(file, 'rb') as f:
            letters_fetched = pickle.load(f)

    # Curate the dictionnary to target
    # It counts wanted autographe with n images and remove the unwanted (if n = -1, nothing is removed)
    for key in loaded:
        if n != -1:
            if (len(loaded[key]) != n):
                continue
        letters_fetched[key] = loaded[key]
        count += 1
    logger.info("Fetched a total of "+str(sum([len(letters_fetched[key]) for key in letters_fetched])
                                          )+" pairs of letter-image, with a total of "+str(count) + " uniques letters")
    return loaded


def __copy_file(filepath: str, dir_target: str, file_rename: str = "") -> None:
    """
    Function for extracting a file, do nothing if the file doesn't exist
    Doesn't check if directory exist !

    Parameters :
        filename :
            The path of the file
        dir_target :
            The path of the output directory
        file_rename :
            The new name for the copied file

    Returns :
        None
    """

    if file_rename and os.path.exists(dir_target+"os.sep"+file_rename):
        # Skip file renamed already exist
        return
    if not file_rename and os.path.exists(dir_target+"os.sep"+filepath):
        # Skip file already extracted
        return

    if os.path.exists(filepath):
        copy(filepath, dir_target)
        if file_rename != "":
            os.rename(dir_target+"os.sep"+filepath,
                      dir_target+"os.sep"+file_rename)


@timeit
def batch_extract_copy(target: dict, output_dir: str = "batch_extract") -> None:
    """
    Extract all images from the target dictionnary to the output_dir

    Parameters :
        target :
            Dictionnary containing the path of wanted images in dict values
        output_dir :
            Directory where file will be copied to

    Returns :
        None
    """
    os.makedirs(output_dir, exist_ok=True)
    for images in target.values():
        for image in images:
            # For each images in the dictionnary's values, extract them to the specified folder
            if os.path.exists(output_dir+os.sep+image) or os.path.exists(output_dir+os.sep+image[:-4]+"_left.jpg"):
                # do not copy if image already extracted
                continue
            copy(image, output_dir)
            # __copy_file(image, output_dir)
    logger.debug(
        "Extracted/copy all target images from dictionnary into "+output_dir)


def extract_column_from_csv(csv_source: str, c1: int, c2: int = -1, list_to_compare: list = []) -> dict:
    """
    Extract value at column c1 from a csv
    where value in column c2 is present in list_to_compare

    Parameters :
        csv_source :
            The path to the CSV
        c1 :
            Index of the column where values will be extracted
        c2 :
            Index of the column where IDs are stored
        list_to_compare :
            List of IDs to compare with column c2

    Returns :
        Dictionnary of ID:value_c1 where c2 value is in list_to_compare
    """
    list_to_compare = sorted(list_to_compare)
    result = {}
    with open(csv_source, newline='', encoding='UTF-8', errors="ignore") as inputfile:

        # Check columns are valid and fetched in a sorted list the data of at column c1 where column c2 valeus are in list_to_compare
        if c1 >= 0 and c2 >= 0:
            csv_data = sorted([(row[c1], row[c2]) for row in csv.reader(
                inputfile) if row[c2] != ""], key=lambda x: x[1])
            i = j = 0
            size_csv, size_lst = len(csv_data), len(list_to_compare)

            # Incremental way of loop through because both list are ordered
            while i < size_csv and j < size_lst:
                if csv_data[i][1] == list_to_compare[j]:
                    result[list_to_compare[j]] = csv_data[i][0]
                    i += 1
                    j += 1
                elif csv_data[i][1] < list_to_compare[j]:
                    i += 1
                else:
                    j += 1
    return result


def move_files_to_parent_directory(parent_folder: str) -> None:
    """
    For each subdirectory move their file into their parent directory
    (Util function, for moving out cropped images from their folder)

    Parameters :
        parent_folder:
            Path to the main directory

    Returns :
        None
    """

    for foldername, subfolders, filenames in list(os.walk(parent_folder))[1:]:
        for filename in filenames:
            filepath = foldername+os.sep+filename
            destination_path = os.sep.join(
                foldername.split(os.sep)[:-1])+os.sep+filename
            move(filepath, destination_path)

    # Remove empty folders
    for folder in list(os.walk(parent_folder)):
        if not folder[2]:
            os.rmdir(folder[0])
            print("rm "+folder[0])


def check_exclude_file(file: str, terms_to_exclude: list, case_sensitive: bool = False) -> bool:
    """
    Verify if the file should be processed or ignored

    Parameters:
        file :
            Filename or filepath to check
        terms_to_exclude :
            List of words indicating the file should be skipped
        case_sensitive :
            If True, exclusion will be case sensitive (default : False)

    Returns:
        True if the filename contains a term to exclude, else return False

    """

    filename = file.split(os.sep)[-1]

    if not case_sensitive:
        for i in range(len(terms_to_exclude)):
            terms_to_exclude[i] = terms_to_exclude[i].lower()
        filename = filename.lower()

    for pattern in terms_to_exclude:
        if pattern in filename:
            return True
    return False


def check_pairs(parent_folder: str) -> bool:
    """
    Inside a folder, will check if every pairs of text-image is present
    Print all image files missing transcription

    Parameters :
        parent_folder:
            Path to the directory to check

    Returns :
        True if every pairs of text-image is present
    """
    dir = list(os.walk(parent_folder))[0]
    files = set(dir[2])
    for filename in files:
        if filename.endswith(".jpg"):
            if filename[:-4]+".gt.txt" not in files:
                print(filename)


if __name__ == "__main__":

    # Utility function that will move out all files from their respective folder
    # It will also print all files missing their transcription file ".gt.txt"
    if len(sys.argv) > 1:
        root_folder = sys.argv[1]
        if not os.path.exists(root_folder):
            pass
        move_files_to_parent_directory(root_folder)
        check_pairs(root_folder)
    pass
# Example
# python3 utils_extract.py ./test/kraken_train/set4/
