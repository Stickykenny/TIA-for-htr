"""
align.py: Contains functions for alignment
"""

import numpy as np
import os
import pickle
import cv2 as cv
import re
import logging
logger = logging.getLogger("align_logger")


def levenshtein_dist(s1: str, s2: str) -> float:
    """
    Compute and return the Levenshtein Distance.
    Algorithm from : https://fr.wikipedia.org/wiki/Distance_de_Levenshtein

    Parameters :
        s1 :
            String 2
        s2 :
            String 2

    Returns :
        The Levenshtein distance of s1 and s2
    """
    m, n = len(s1)+1, len(s2)+1

    d = [[0]*(n) for i in range(m)]

    """
    for i in range(m) :
        D[i][0] = i
    for j in range(n) :
        D[0][j] = j
    """

    for j in range(1, n):
        for i in range(1, m):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            d[i][j] = min(
                d[i-1][j]+1,  # effacement du nouveau caractère de s1
                d[i][j-1]+1,  # insertion dans s2 du nouveau caractère de s1
                d[i-1][j-1]+cost)  # substitution

    for i in d:
        # print(i)
        pass
    return d[m-1][n-1]


def lis(arr: list) -> tuple[int, list[int]]:
    """
    Longuest increasing sequence, dynamic programming

    Parameters :
        arr :
            The array

    Returns :
        The LIS value and his matrix
    """
    n = len(arr)
    lis = [1]*n

    for i in range(1, n):
        for j in range(0, i):
            if arr[i] > arr[j] and lis[i] < lis[j] + 1:
                lis[i] = lis[j]+1

    return max(lis), lis


def txt_compare_open(image_filename: str) -> tuple[str, list[str]]:
    """
    Retrieve the ocr result and the transcription of the filename

    Parameters:
        image_filename:
            Name of the image file

    Returns:
        A string of the transcription and a list of every pattern found by the ocr
    """

    name_pattern = re.compile("\d+(?:-\d+)*")
    cote = name_pattern.search(image_filename).group(0)

    txt_manual_file = "tmp"+os.sep+"extract_txt"+os.sep+cote+".gt.txt"
    txt_ocr_file = "tmp"+os.sep+"ocr_result" + \
        os.sep+image_filename[:-4]+"_ocr.txt"

    with open(txt_manual_file, newline='') as inputfile:
        txt_manual = inputfile.readlines()
        txt_manual.pop()  # Remove last line which is autographe reference
        txt_manual = ''.join(txt_manual).replace('\t', '').replace('\n', '')

    with open(txt_ocr_file, newline='') as inputfile:
        txt_ocr = inputfile.readlines()
        txt_ocr = [txt.replace('\t', '').replace('\n', '') for txt in txt_ocr]

    return txt_manual, txt_ocr


def align_patterns(patterns: str, text: str, printing: bool = False) -> tuple[dict, list]:
    """
    Find the best alignment for each pattern

    Parameters:
        pattern:
            List of all pattern to test
        text:
            Text in which the pattern are located
        printing:
            If True result will be printed on terminal

    Returns:
        A list of [pattern, pattern_index, text_matched, distance_score] and his list of index indicating where these match are in the text
    """

    indexes = []
    # associations = [ [pattern, pattern_index, text_matched, distance score]  , [ ... ] , ... ]
    associations = []
    pattern_index = 0
    for pattern in patterns:
        scores = []
        for i in range(len(text)-len(pattern)):
            scores.append(levenshtein_dist(pattern, text[i:i+len(pattern)]))
        index = np.argmin(scores)
        if scores[index] < len(pattern)//1.5:

            # Complete words
            def complete_word(text, lower_bound, upper_bound):
                character = text[lower_bound]
                while not character == " ":
                    lower_bound -= 1
                    character = text[lower_bound]

                character = text[upper_bound]
                while not character == " ":
                    upper_bound += 1
                    character = text[upper_bound]

                return text[lower_bound:upper_bound]
            text_match = complete_word(text, index, index+len(pattern))

            associations.append([
                pattern, pattern_index, text_match, scores[index]])
            indexes.append(index)

            if printing:
                logger.debug("For : "+str(pattern)+" | >> dist score : " +
                             str(scores[index]) + "\t\t\t at index : "+str(index))
                logger.debug("\t "+text_match)
        pattern_index += 1
    return associations, indexes


def get_usable_alignments(associations: dict[str, int, str, int], indexes: list[int]) -> tuple[dict, list]:
    """
    Use LIS(Longuest Increasing Sequence) to remove alignments that are likely wrong

    Parameters:
        associations:
            A list of [pattern, pattern_index, text_matched, distance_score]
        indexes:
            The list of index indicating where these match are in the text

    Returns:
        A list of usable [pattern, pattern_index, text_matched, distance_score] and his list of index indicating where these match are in the original list
    """
    # TODO
    return associations, indexes
    itr, lis_result = lis(indexes)
    lst = list()
    index_used = []
    for i in range(len(associations)-1, -1, -1):
        if itr == 0:
            break
        if itr == lis_result[i]:
            lst.append(associations[i])
            index_used.append(i)
            itr -= 1

    lst = list(reversed(lst))
    index_used = list(reversed(index_used))
    return lst, index_used


def align_cropped(lst: list[str, int, str, int], filepath: str) -> None:
    """
    For each alignment, create the pair text-image

    Parameters:
        lst:
            A list of curated [pattern, pattern_index, text_matched, distance_score]
        filepath:
            path to the original image

    Returns:
        A list of usable [pattern, pattern_index, text_matched, distance_score] and his list of index indicating where these match are in the original list
    """
    filename = filepath.split(os.sep)[-1]
    # Fetch position of segmented motif
    predict_backup = "tmp"+os.sep+"save"+os.sep + \
        "ocr_save"+os.sep+filename+'_ocr.pickle'
    with open(predict_backup, 'rb') as file:
        predictions = pickle.load(file)

    cropping_dir = "tmp"+os.sep+"cropped_match"+os.sep+filename
    os.makedirs(cropping_dir, exist_ok=True)

    img = cv.imread(filepath, cv.IMREAD_COLOR)
    # Align text-image for crop
    name_iterator = 0

    for i in range(len(lst)):
        # Crop the image
        boundaries = predictions[lst[i][1]].line
        x_min = x_max = boundaries[0][0]
        y_min = y_max = boundaries[0][1]
        for j in range(1, len(boundaries)):
            x = boundaries[j][0]
            y = boundaries[j][1]
            x_min = (x if x < x_min else x_min)
            x_max = (x if x > x_max else x_max)
            y_min = (y if y < y_min else y_min)
            y_max = (y if y > y_max else y_max)
        cropped = img[y_min:y_max, x_min:x_max]
        cropped_img_path = cropping_dir+os.sep + \
            filename[:-4]+"_"+str(name_iterator)+".jpg"
        cv.imwrite(cropped_img_path, cropped)

        # Create txt file associated
        with open(cropped_img_path[:-4]+'.gt.txt', 'w') as f:
            f.write(lst[i][2])
        name_iterator += 1
    logger.debug("Finished cropping "+str(name_iterator) +
                 " times for "+filename)


def batch_align_crop(image_dir, printing=False, specific_input=None) -> None:
    logger.info("Started batch align text-images with segmented images")
    if specific_input == None:
        # Process the entire directory
        # TODO  proof when multiple images per cotes
        for (dirpath, subdirnames, filenames) in os.walk(image_dir):
            for filename in filenames:
                filepath = dirpath+os.sep+filename

                try:
                    txt_manual, txt_ocr = txt_compare_open(filename)
                except:
                    continue
                logger.info("Align " + filepath)
                associations, indexes = align_patterns(
                    txt_ocr, txt_manual, printing)
                lst_alignments_usable, index_used = get_usable_alignments(
                    associations, indexes)
                align_cropped(lst_alignments_usable, index_used, filepath)
    else:
        # Process only specified images
        for cote in specific_input:
            for filepath in specific_input[cote]:
                print(filepath)
                filename = filepath.split(os.sep)[-1]
                logger.info("Align " + filepath)
                txt_manual, txt_ocr = txt_compare_open(filename)
                associations, indexes = align_patterns(
                    txt_ocr, txt_manual, printing)
                lst_alignments_usable, index_used = get_usable_alignments(
                    associations, indexes)
                align_cropped(lst_alignments_usable, index_used, filepath)


if __name__ == "__main__":

    main_dir = "tmp/extract_image"

    batch_align_crop(main_dir)
