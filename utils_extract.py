"""
Extra Scripts and functions
"""
from monitoring import timeit
from ast import literal_eval
import os
from shutil import copy
import csv
from gdown import download as gdown_download
import logging
logger = logging.getLogger("align_logger")


def get_column_values(csv_source: str, column: int = 9) -> list[str]:
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
    with open(csv_source, newline='') as inputfile:
        return [row[column] for row in csv.reader(inputfile) if row[column] != ""]


def get_letter_with_n_image(file: str, n: int = -1) -> dict[str, list[str]]:
    """
    Retrieve all letters' cote having only n image
    if n = -1, this function will simply convert the file into a python dictionnary

    Parameters :
        file :
            The path of the file containing a dict
        n : 
            The sound the animal makes

    Returns :
        The dictionnary {cote->[images]} of every letter having n images
    """

    letters_fetched = dict()
    count = 0
    with open(file, 'r') as f:
        for line in f.readlines():
            line = line.split(":")
            retrieved_list = literal_eval(line[1])
            if n != -1:
                if (len(retrieved_list) != n):
                    continue
            # print(line[0]+","+str(retrieved_list))
            letters_fetched[line[0]] = retrieved_list
            count += 1
    logger.info("Fetched a total of "+str(count) +
                " pairs of letter-image, with a total of "+str(len(letters_fetched))+" uniques letters")
    return letters_fetched


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
    for item in target.items():
        for image in [img for img in item[1]]:
            __copy_file(image, output_dir)
    logger.debug(
        "Extracted/copy all target images from dictionnary into "+output_dir)


def extract_column_from_csv(csv_source: str, c1: int, c2: int = -1, list_to_compare: list[str] = []) -> dict[str:str]:
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
    with open(csv_source, newline='') as inputfile:
        if c1 >= 0 and c2 >= 0:
            csv_data = sorted([(row[c1], row[c2]) for row in csv.reader(
                inputfile) if row[c2] != ""], key=lambda x: x[1])
            i = j = 0
            size_csv, size_lst = len(csv_data), len(list_to_compare)
            # Incremental way of loop through
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


def batch_download_pdf_gdrive(links: dict, output_dir: str = "", quiet: int = 1, name_associated: dict = None):
    """
    Currently programmed for pdf associated with only 1 image
    """
    print("DEPRECATED, avoiding automation of google services")
    raise AssertionError("DEPRECATED, avoiding automation of google services")
    return
    output_dir_checker = output_dir != ""
    quiet_download = True if quiet < 2 else False
    os.makedirs(output_dir, exist_ok=True)

    for item in links.items():
        # TODO Check if already exists
        url = item[1]
        # By default, name of the pdf will be the cote
        output_name = item[0]
        if name_associated:
            output_name = name_associated[item[0]][0].split(os.sep)[-1]
        if (output_dir_checker):
            output_name = output_dir+os.sep + output_name[:-4]+".pdf"

        if quiet >= 1:
            print("Downloading > "+str(item)+" to "+output_name)
        gdown_download(url=url, output=output_name,
                       quiet=quiet_download, fuzzy=True)


if __name__ == "__main__":

    letters_fetched = get_letter_with_n_image("result.txt", 1)
    batch_extract_copy(letters_fetched)

    csv_source = 'Correspondance MDV - Site https __www.correspondancedesbordesvalmore.com - lettres.csv'
    print("extract link")
    links = extract_column_from_csv(csv_source, c1=3, c2=9,
                                    list_to_compare=list(letters_fetched.keys()))
    print(links)
    batch_download_pdf_gdrive(links, output_dir="test/extract_pdf")
