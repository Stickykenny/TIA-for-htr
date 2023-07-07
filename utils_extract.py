"""
Extra Scripts and functions
"""
from ast import literal_eval
import os
from shutil import copy
import csv
from gdown import download as gdown_download


def get_column_values(csv_source: str, column: int = 9) -> list[str]:
    """
    Retrieve into a list all values from the n column
    """
    with open(csv_source, newline='') as inputfile:
        return [row[column] for row in csv.reader(inputfile) if row[column] != ""]


def get_letter_with_n_image(filename: str, n: int = 0) -> dict:
    """
    Print all letters' cote having only n image
    if n = 0, this function will simply convert the file into a python dictionnary
    """
    letters_fetched = dict()
    with open(filename, 'r') as f:
        for line in f.readlines():
            line = line.split(":")
            retrieved_list = literal_eval(line[1])
            if n != 0:
                if (len(retrieved_list) != n):
                    continue
            # print(line[0]+","+str(retrieved_list))
            letters_fetched[line[0]] = retrieved_list
    return letters_fetched


def __copy_file(filename, dir_target, file_rename: str = ""):
    """
    Function for extracting a file, do nothing if the file doesn't exist
    Doesn't check if directory exist !
    """
    if os.path.exists(filename):
        copy(filename, dir_target)
        if file_rename != "":
            os.rename(dir_target+"os.sep"+filename,
                      dir_target+"os.sep"+file_rename)


def batch_extract_copy(target: dict, output_dir: str = "batch_extract"):
    """
    Extract all images from the target dictionnary to the output_dir
    """
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    for item in target.items():
        print(item)
        for image in [img for img in item[1]]:
            __copy_file(image, output_dir)


def extract_filelink_from_drive(csv_source: str, c1: int, c2: int = -1, list_to_compare: list[str] = []):
    """
    Extract file at column c1 from google sheet
    where value in column c2 is present in list_to_compare
    """
    list_to_compare = sorted(list_to_compare)
    result = {}
    with open(csv_source, newline='') as inputfile:
        if c1 >= 0 and c2 >= 0:
            csv_data = sorted([(row[c1], row[c2]) for row in csv.reader(
                inputfile) if row[c2] != ""], key=lambda x: x[1])
            i = j = 0
            size_csv, size_lst = len(csv_data), len(list_to_compare)
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


def batch_download_pdf_gdrive(links: dict, output_dir: str = "", quiet: int = 1):
    """
    Currently programmed for pdf associated with only 1 image
    """
    output_dir_checker = output_dir != ""
    quiet_download = True if quiet < 2 else False
    if output_dir_checker:
        os.makedirs(output_dir, exist_ok=True)

    for item in links.items():
        if quiet >= 1:
            print("Downloading > "+str(item))
        url = item[1]
        if (output_dir_checker):
            gdown_download(url=url, output=output_dir+os.sep +
                           item[0]+".pdf", quiet=quiet_download, fuzzy=True)
        else:
            gdown_download(
                url=url, output=item[0]+".pdf", quiet=quiet_download, fuzzy=True)

        pass


if __name__ == "__main__":

    letters_fetched = get_letter_with_n_image("result.txt", 1)
    batch_extract_copy(letters_fetched)

    csv_source = 'Correspondance MDV - Site https __www.correspondancedesbordesvalmore.com - lettres.csv'
    print("extract link")
    links = extract_filelink_from_drive(csv_source, c1=3, c2=9,
                                        list_to_compare=list(letters_fetched.keys()))
    print(links)
    batch_download_pdf_gdrive(links, output_dir="test/extract_pdf")
