from collections import Counter
from monitoring import timeit
import os
import shutil
import random
import ujson
import logging
logger = logging.getLogger("TIA_logger")


def split_dataset(source_dir: str, partition: int = 0.9, newset_name: str = "") -> str:
    """
    Split the targeted dataset into a new set by moving out randomly chosen data

    Parameters :
        source_dir :
            Path to the folder containing the dataset
        partition : 
            Data partition ratio between, the ,normalized number given will be the number of data kept
        newset_name : 
            The name of the folder where data will be moving into. If the folder already has files, the setname will be appended a number [same way as the default name]
            (Default : a generated name setX, where X is a number incrementing until the path is free to occupy )

    Returns :
        Path of the new splitted dataset
    """

    # Retrieve parent folder path, for the new set save location
    path_to_parent = os.path.dirname(os.path.abspath(source_dir))

    # Create directory where the splitted data will be moving to
    # If no name has been decided, default name will be setX, where X is the smallest natural number non-taken
    newset_path = path_to_parent+os.sep+newset_name
    name_count = 1
    newset_path += "_0"
    if newset_name:
        while os.path.exists(newset_path) and os.listdir(newset_path) != []:
            newset_path = newset_path[:-len(str(name_count+1))]+str(name_count)
            name_count += 1
        os.makedirs(newset_path, exist_ok=True)
        newset_name = newset_path.split(os.sep)[-1]
    else:
        newset_path = path_to_parent+os.sep+"set"+str(name_count)
        # Until the setname is available, increment the name_count
        while os.path.exists(newset_name):
            newset_path = path_to_parent+os.sep+"set"+str(name_count)
            name_count += 1
        newset_name = newset_path.split(os.sep)[-1]

    # Retrieve the main dataset
    main_dataset = list()
    for dir, subfolders, files in os.walk(source_dir):
        main_dataset.extend([dir+os.sep+file
                            for file in files if file.endswith(".jpg")])

    # Split the dataset given partition
    main_size = len(main_dataset)//2
    new_set = (random.sample(main_dataset, int(main_size*(1-partition))))
    # main_dataset -= set(new_set)

    # Move splitted data into their separate folders
    path_diff = os.path.abspath(source_dir).replace(path_to_parent, "")

    moved_count = 0
    for imagepath in new_set:

        # Obtain the new path
        new_imagepath = path_to_parent+os.sep + newset_name+os.sep + \
            imagepath.replace(path_diff, "#").split("#")[-1]
        new_textpath = new_imagepath[:-4]+".gt.txt"

        # Create output folders if missing
        os.makedirs(os.path.dirname(new_imagepath), exist_ok=True)

        # Move image and text file
        shutil.move(imagepath, new_imagepath)
        shutil.move(imagepath[:-4]+".gt.txt", new_textpath)
        moved_count += 1

    logger.info("Moved a total of "+str(moved_count) +
                " pairs of text/image to create the "+newset_name+" folder.")
    return path_to_parent+os.sep+newset_name


if __name__ == '__main__':
    split_dataset("tmp/cropped_match", partition=0.8,
                  newset_name="test_dataset")
    pass
