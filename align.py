"""
align.py: Contains functions for alignment
"""

import numpy as np
import os
import pickle
import cv2 as cv
import re
from monitoring import timeit
import ujson
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

    # Init all values of matrix with zeros
    d = [[0]*(n) for i in range(m)]

    # Init at 0, so that the word can start anywhere, so this block is commented
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
                d[i-1][j]+1,  # deletion of the new character of s1
                d[i][j-1]+1,  # insertion in s2 of the new character of s1
                d[i-1][j-1]+cost)  # substitution

    return d[m-1][n-1], d


def calculate_error_rate(pattern: str, reference: str, percent: bool = False):
    """
    Calculate Word Error Rate and Character Error Rate

    Parameters :
        pattern :
            pattern to test
        reference :
            Reference to compare to
        percent :
            If True, result will be in percent

    Returns :
        The WER and the CER
    """
    pattern_words = pattern.split()
    ref_words = reference.split()

    wer = levenshtein_dist(pattern_words, ref_words)[0]/len(ref_words)
    cer = levenshtein_dist(pattern, reference)[0]/len(reference)
    if percent:
        wer, cer = wer*100, cer*100
    return wer, cer


def lis(arr: list) -> tuple:
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


def hamming_distance(string1: str, string2: str) -> int:
    """
    Calculate the Hamming Distance between 2 strings

    Parameters:
        string1 :
            The first string
        string2 :
            The second string

    Returns:
        the Hamming Distance between 2 strings
    """
    return sum(c1 != c2 for c1, c2 in zip(string1, string2))


def txt_compare_open(image_filename: str) -> tuple:
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

    # Retrieve filepath of the ocr and manual transcription form the image filename
    txt_manual_file = "tmp"+os.sep+"extract_txt"+os.sep+cote+".gt.txt"
    txt_ocr_file = "tmp"+os.sep+"ocr_result" + \
        os.sep+image_filename[:-4]+"_ocr.txt"

    # Retrieve the manual transcription without tab and newline
    with open(txt_manual_file, newline='') as inputfile:
        txt_manual = inputfile.readlines()
        txt_manual.pop()  # Remove last line which is autographe reference
        txt_manual = ''.join(txt_manual).replace('\t', '').replace('\n', '')

    # Retrieve the ocr prediction into a list of each segmented part
    with open(txt_ocr_file, newline='') as inputfile:
        txt_ocr = inputfile.readlines()
        txt_ocr = [txt.replace('\t', '').replace('\n', '') for txt in txt_ocr]

    return txt_manual, txt_ocr


def complete_word(corpus: str, lower_bound: int, upper_bound: int, threshold: int = -1) -> str:
    """
    Will try to complete words by extending range up to threshold amount of character

    Parameters:
        corpus:
            Corpus where the text is from
        lower_bound:
            index where the extracted text starts
        upper_bound:
            index where the extracted text ends
        threshold:
            Maximum number of characters to extend to complete a word
            (By default : -1, negative value will complete the word no matter how long it is) 

    Returns:
        Text processed that may be extended
    """

    # Will extend upper and lower bound until a word separator if encountered
    word_separator = [" ", ",", ""]

    new_upper = upper_bound
    new_lower = lower_bound
    character = corpus[new_lower]
    while character not in word_separator:
        new_lower -= 1
        character = corpus[new_lower]

    character = corpus[new_upper]
    while character not in word_separator:
        new_upper += 1
        character = corpus[new_upper]

    # Threshold check, to not extend too much
    if threshold >= 0:
        if lower_bound - new_lower >= threshold:
            # should not complete more than threshold characters
            new_lower = lower_bound
        if new_upper - upper_bound >= threshold:
            # should not complete more than threshold characters
            new_upper = upper_bound

    return corpus[new_lower:new_upper]


@timeit
def align_patterns(patterns: str, text: str, printing: bool = True) -> tuple:
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

    # For each pattern found by the ocr
    # 1/ Align them in the original text using hamming distance
    # 2/ With the best match, complete word if necessary
    for pattern in patterns:
        scores = []
        for i in range(len(text)-len(pattern)):
            scores.append(hamming_distance(pattern, text[i:i+len(pattern)]))
        index = np.argmin(scores)

        # A distance too great too great is ignored
        if scores[index] < len(pattern)//1.5:

            if not pattern or pattern.isspace():
                # Skip empty ocr
                continue

            # Complete words
            text_complete = complete_word(text, index, index+len(pattern))

            associations.append([
                pattern, pattern_index, text_complete, scores[index]])
            indexes.append(index)

            # if True, if will log a trace of every alignment done ( cause a lot of logs )
            if printing:
                wer, cer = calculate_error_rate(pattern, text, percent=True)
                logger.debug("For : "+str(pattern)+" | >> dist score : " +
                             str(scores[index]) + "\t\t\t at index : "+str(index))
                logger.debug("\t "+text_complete)
                logger.debug("WER : "+str(wer) +
                             ", CER : "+str(cer))

        pattern_index += 1
    return associations, indexes


def get_usable_alignments(associations: dict, indexes: list) -> tuple:
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


def align_cropped(lst: list, filepath: str, checklist: set) -> None:
    """
    For each alignment, create the pair text-image

    Parameters:
        lst:
            A list of curated [pattern, pattern_index, text_matched, distance_score]
        filepath:
            path to the original image
        checklist:
            Set of all images already cropped

    Returns:
        None    
    """

    filename = filepath.split(os.sep)[-1]

    # Fetch position of segmented pattern from pickled save of an ocr_record
    predict_backup = "tmp"+os.sep+"save"+os.sep + \
        "ocr_save"+os.sep+filename+'_ocr.pickle'
    with open(predict_backup, 'rb') as file:
        predictions = pickle.load(file)

    cropping_dir = "tmp"+os.sep+"cropped_match"+os.sep+filename
    os.makedirs(cropping_dir, exist_ok=True)

    # Check if cropped are already done
    files_cropping_dir = [file for file in os.walk(cropping_dir)][0][2]
    if len(files_cropping_dir) == 2*len(lst):
        logger.debug("Cropped are already present in "+cropping_dir)

    else:
        # Align text-image for crop
        img = cv.imread(filepath, cv.IMREAD_COLOR)
        name_iterator = 0

        for i in range(len(lst)):
            # Crop the image
            boundaries = predictions[lst[i][1]].line
            x_min = x_max = boundaries[0][0]
            y_min = y_max = boundaries[0][1]
            for j in range(1, len(boundaries)):
                x = boundaries[j][0]
                y = boundaries[j][1]

                # Take larger coordinates for a rectangle cropping
                x_min = (x if x < x_min else x_min)
                x_max = (x if x > x_max else x_max)
                y_min = (y if y < y_min else y_min)
                y_max = (y if y > y_max else y_max)

            # If the text matched is empty, skip
            if not lst[i][2]:
                continue

            # Create cropped file associated
            cropped = img[y_min:y_max, x_min:x_max]
            cropped_img_path = cropping_dir+os.sep + \
                filename[:-4]+"_"+str(name_iterator)+".jpg"
            cv.imwrite(cropped_img_path, cropped)

            # Create txt file associated
            with open(cropped_img_path[:-4]+'.gt.txt', 'w') as f:
                f.write(lst[i][2])
            name_iterator += 1
        logger.debug("Finished cropping " +
                     str(name_iterator) + " times for "+filename)

    # Update checklist to indicate this crop is done
    with open("tmp"+os.sep+"save"+os.sep+"cropped_checklist.json", "r") as file:
        checklist = ujson.load(file)
        checklist.append(cropping_dir)
    with open("tmp"+os.sep+"save"+os.sep+"cropped_checklist.json", "w") as file:
        ujson.dump(checklist, file, indent=4)

    logger.debug("Added "+cropping_dir + " to the checklist of cropped image")


@timeit
def batch_align_crop(image_dir: str, printing: bool = False, specific_input: dict = None) -> None:
    """
    Batch process image files to create pairs of alignments text-images

    Parameters:
        image_dir:
            Directory where images are located
        printing:
            If True, logger will log in debug of each text-image alignment with their score
        specific_input:
            Dictionary to specify specific images to process instead of all images in a directory 

    Returns:
        None    
    """
    logger.info("Started batch align text-images with segmented images")
    count = 0

    # Use a list to verify whether the text-image alignment is already done for a file
    checklist_path = "tmp"+os.sep+"save"+os.sep+"cropped_checklist.json"
    if not (os.path.exists(checklist_path) or os.path.isfile(checklist_path)):
        # Create new empty checklist is one doesn't exist
        checklist = set()
        with open(checklist_path, "w") as file:
            ujson.dump(checklist, file)
    else:
        with open(checklist_path, "r") as file:
            checklist = ujson.load(file)

    # Verify checklist folder is still correct
    # TODO

    if specific_input == None:
        # Process the entire directory
        for (dirpath, subdirnames, filenames) in os.walk(image_dir):
            for filename in filenames:
                filepath = dirpath+os.sep+filename

                # Process the entire directory, thism ay cause error due to image present but not yet ocr-ed
                try:
                    count = apply_align(
                        count, filename, filepath, checklist)
                except:
                    logger.warning(
                        "Error trying to align this file : "+filepath)

    else:
        # Process only specified images
        for cote in specific_input:
            for filepath in specific_input[cote]:
                filename = filepath.split(os.sep)[-1]
                count = apply_align(
                    count, filename, filepath, checklist)


def apply_align(count: int, filename: str, filepath: str, checklist: set = None) -> int:
    """
    Apply alignment to create pairs of text-images

    Parameters:
        count:
            Current count of images aligned (for statistic purpose)
        filename :
            Name of the image file
        filepath :
            Path to the image file
        checklist:
            Set of all images already cropped

    Returns:
        count + 1    
    """

    # Check if image was already cropped and aligned, then no need to align
    if checklist and ("tmp"+os.sep+"cropped_match"+os.sep + filename) in checklist:
        return count

    logger.info("Align " + filepath)
    # Fetch the manual transcription and the ocr
    try:
        txt_manual, txt_ocr = txt_compare_open(filename)
    except Exception as Argument:
        logger.warning("Error loading text for alignment : "+str(Argument))
        return count

    # Align each pattern of the ocr to the transcription
    associations, indexes = align_patterns(
        txt_ocr, txt_manual)

    # TODO When implemented will curate the alignments
    lst_alignments_usable, index_used = get_usable_alignments(
        associations, indexes)

    # Crop and produce every pair of text-image
    align_cropped(lst_alignments_usable, filepath, checklist)

    count += 1
    logger.debug("Cropped a total of "+str(count)+" images")
    return count


if __name__ == "__main__":

    main_dir = "tmp/extract_image"

    batch_align_crop(main_dir)
