"""
Extra Scripts and functions
"""
from ast import literal_eval
import os 
from shutil import copy

def get_letter_with_n_image(filename : str, n : int=1)-> dict :
    """
    Print all letters' cote having only n image
    if n = 0, this function will simply convert the file into a python dictionnary
    """
    letters_fetched = dict()
    with open(filename, 'r') as f:
        for line in f.readlines() :
            line = line.split(":")
            retrieved_list = literal_eval(line[1])
            if n != 0 :
                if (len(retrieved_list) != n) :
                    continue
            print(line[0]+","+str(retrieved_list))
            letters_fetched[0]= retrieved_list
    return letters_fetched

def __copy_file(filename, dir_target, file_rename : str = "") :
    """
    Function for extracting a file, do nothing if the file doesn't exist
    Doesn't check if directory exist !
    """
    if os.path.exists(filename) :    
        copy(filename, dir_target)
        if file_rename != "" :
            os.rename(dir_target+"os.sep"+filename,dir_target+"os.sep"+file_rename)

def batch_extract_copy(target : dict , output_dir : str="batch_extract") :
    """
    Extract all images from the target dictionnary in the inpur_dir to the output_dir
    """
    if not os.path.isdir(output_dir) :
        os.mkdir(output_dir)
    for item in target.items() :
        for images in item[1] :
            for image in images :
                __copy_file(image,output_dir)

if __name__ == "__main__" :

    __copy_file('Images/Ms 1620-1.jpg/Ms1620-1-10.jpg', "batch")