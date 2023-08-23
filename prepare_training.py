"""
usage : python3 prepare_training.py

Split files of a directory into another directory
"""

import os
import shutil
import random
import logging
logger = logging.getLogger("TIA_logger")



def split_dataset(source_dir: str, partition: int = 0.9, newset_name: str = "split_dataset") -> str:
    """
    Split the targeted dataset into a new set by moving out randomly chosen data

    Parameters :
        source_dir :
            Path to the folder containing the dataset
        partition : 
            Data partition ratio between, the ,normalized number given will be the number of data kept
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
    
    if os.path.exists(newset_path) :
        print("Split folder already exists")
        return 
    
    os.makedirs(newset_path, exist_ok=True)
    newset_name = newset_path.split(os.sep)[-1]

    # Retrieve the main dataset
    main_dataset = list()
    for directory, subfolders, files in os.walk(source_dir):
        main_dataset.extend([directory+os.sep+file
                            for file in files if file.endswith((".jpg",".png"))])

    new_set = (random.sample(main_dataset, int(len(main_dataset)*(partition))))

    # Move splitted data into their separate folders
    path_diff = os.path.abspath(source_dir).replace(path_to_parent, "")

    moved_count = 0
    for imagepath in new_set:

        # Obtain the new path
        new_imagepath = path_to_parent+os.sep + newset_name+os.sep + \
            imagepath.replace(path_diff, "#").split("#")[-1]
        new_textpath = new_imagepath[:-4]+".txt"

        # Create output folders if missing
        os.makedirs(os.path.dirname(new_imagepath), exist_ok=True)

        # Move image and text file
        try :
            
            shutil.move(imagepath, new_imagepath)
            shutil.move(imagepath[:-4]+".txt", new_textpath)
            moved_count += 1
        except : 
            print("Error moving "+imagepath)
            continue
        

    print("Moved a total of "+str(moved_count) +
                " pairs of text/image to create the "+newset_name+" folder.")
    return path_to_parent+os.sep+newset_name


if __name__ == '__main__':
    split_dataset("tmp/extract_image", partition=0.005,
                  newset_name="split_dataset")
    pass
