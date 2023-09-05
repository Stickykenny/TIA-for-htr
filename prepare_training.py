"""
This file is used for splitting a set of data (image jpg with their transcription .gt.txt)

Usage : add_align.py <path_to_set> [partition_ratio] [new_dataset_folder_name]

Arguments:
    path_to_set               Path of the set to split
    partition_ratio           Ratio of the split (default : 0.2)
    new_dataset_folder_name   Name of the folder created
"""

import os
import shutil
import random
import sys
import logging
logger = logging.getLogger("TIA_logger")


def split_dataset(source_dir: str, partition: float = 0.2, newset_name: str = "split_dataset") -> str:
    """
    Split the targeted dataset into a new set by moving out randomly chosen data

    Parameters :
        source_dir :
            Path to the folder containing the dataset
        partition : 
            Data partition ratio that will be moved out
        newset_name : 
            The name of the folder where data will be moving into. If the folder already exists do nothing.

    Returns :
        Path of the new splitted dataset
    """

    # Retrieve parent folder path, for the new set save location
    path_to_parent = os.path.dirname(os.path.abspath(source_dir))

    # Create directory where the splitted data will be moving to
    #  If the folder already exists do nothing.
    newset_path = path_to_parent+os.sep+newset_name

    if os.path.exists(newset_path):
        print("Split folder already exists")
        return

    os.makedirs(newset_path, exist_ok=True)
    newset_name = newset_path.split(os.sep)[-1]

    # Retrieve the main dataset
    main_dataset = list()
    for directory, subfolders, files in os.walk(source_dir):
        main_dataset.extend([directory+os.sep+file
                            for file in files if file.endswith((".jpg", ".png"))])

    # Select randomly files
    new_set = (random.sample(main_dataset, int(len(main_dataset)*(partition))))

    # Move splitted data into their separate folders
    path_diff = os.path.abspath(source_dir).replace(path_to_parent, "")

    moved_count = 0
    for imagepath in new_set:

        # Obtain the new path
        new_imagepath = path_to_parent+os.sep + newset_name+os.sep + \
            imagepath.split(path_diff)[-1]
        new_textpath = new_imagepath[:-4]+".gt.txt"

        # Create output folders if missing
        os.makedirs(os.path.dirname(new_imagepath), exist_ok=True)

        # Move image and text file
        try:

            shutil.move(imagepath, new_imagepath)
            shutil.move(imagepath[:-4]+".gt.txt", new_textpath)
            moved_count += 1
        except:
            print("Error moving "+imagepath)
            continue

    print("Moved a total of "+str(moved_count) +
          " pairs of text/image to create the "+newset_name+" folder.")
    return path_to_parent+os.sep+newset_name


def script_error():
    """
    Print the documentation of this file then exit
    """
    print(__doc__)
    sys.exit()


if __name__ == '__main__':

    try:
        # Script must have at least one argument
        if len(sys.argv) < 1:
            print("Please indicate in the first argument the folder to split")
            script_error()

        if os.path.exists(sys.argv[1]) and not os.path.exists(sys.argv[1]):
            print("Please indicate a correct folder path for the split task")
            script_error()

        pairs_folder = sys.argv[1]

        if len(sys.argv) < 2:
            split_dataset(pairs_folder)

        partition_ratio = float(sys.argv[2])
        if len(sys.argv) < 3:
            split_dataset(pairs_folder, partition=partition_ratio)
        split_name = str(sys.argv[3])
        split_dataset(pairs_folder, partition=partition_ratio,
                      newset_name=split_name)

    except:
        print(__doc__)
        sys.exit()
