import os
import re
import time
from utils_extract import get_column_values

image_extension = (".jpg", ".png", ".svg", "jpeg")


def fetch_images(directory: str, path: bool, recursive: bool = True) -> list[str]:
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
    # Create the dictionnary of {cote:autographe}
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


def get_matches(autographes: list[str], images_files: list[str]) -> tuple[int, dict]:

    count = 0
    cotes_availables = {}

    files = sorted([i for i in images_files if i.split(
        os.sep)[-1].lower().startswith("ms")])
    current_size = len(files)
    i = 0
    # To find matches more efficiently, we remove images found associated
    while i < current_size:
        cotes, count, cotes_availables, files, current_size, i = __compare_match(
            cotes, count, cotes_availables, files, current_size, i)
    return count, cotes_availables


def __compare_match(cotes, count, cotes_availables, files, current_size, i):
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


def get_length_list_dict(dictionnary: dict) -> int:
    length = 0
    for item in dictionnary.values():
        length += len(item)
    return length

# Dictionnaire
# cotes : [ code : nom complet de l'autographe ]
# cotes_available : [ code : [ liste des noms de fichiers images ]]


if __name__ == "__main__":

    path = False  # If True, result will show images relative path instead of just the filename

    # Retrieve csv data
    csv_source = 'Correspondance MDV - Site https __www.correspondancedesbordesvalmore.com - lettres.csv'
    autographes = get_column_values(csv_source, column=9)

    # Statistics
    total_found = 0
    letters_associated = 0

    # Reset result output
    if os.path.exists("result.txt"):
        os.remove("result.txt")

    for dir in next(os.walk('Images'))[1]:
        path_images_dir = "Images/"+dir

        images_files = fetch_images(path_images_dir, path)
        print("For the folder  > "+path_images_dir)
        print("Image count > " + str(len(images_files)) + "| Timer starting now ")
        start_time = time.time()

        cotes = indexing_autographes(autographes)
        found_matches, cotes_associated = get_matches(cotes, images_files)

        print("Matches found  > " + str(found_matches) +
              " | Time taken : " + str(time.time() - start_time))

        with open("result.txt", 'a+') as f:
            for i in cotes_associated.items():
                f.write(str(i[0])+":"+str(i[1])+"\n")

        # Statistics
        total_found += found_matches
        letters_associated += len(cotes_associated)
        print("--------------------")
    print("Found in total "+str(total_found)+" matches of images with letter\nTotalling " +
          str(letters_associated)+" letters associated")
