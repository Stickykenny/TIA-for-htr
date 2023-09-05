"""
align.py: Contains functions for alignment
"""

import numpy as np
import os
import pickle
import cv2 as cv
import re
from monitoring import timeit
import shutil
import logging
logger = logging.getLogger("TIA_logger")


image_extension = (".jpg", ".png")


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

    for i in range(m):
        d[i][0] = i
    for j in range(n):
        d[0][j] = j

    for j in range(1, n):
        for i in range(1, m):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            d[i][j] = min(
                d[i-1][j]+1,  # deletion of the new character of s1
                d[i][j-1]+1,  # insertion in s2 of the new character of s1
                d[i-1][j-1]+cost)  # substitution

    return d[m-1][n-1], d


def calculate_error_rate(pattern, reference, norm=True, percent=False):
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

    wer = levenshtein_dist(pattern_words, ref_words)[0]
    cer = levenshtein_dist(pattern, reference)[0]
    if norm or percent:
        if len(ref_words):
            wer = wer/len(ref_words)
        if len(reference):
            cer = cer/len(reference)
    if percent:
        wer, cer = wer*100, cer*100
    return wer, cer


def lis(arr: list) -> tuple:
    """
    UNUSED
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

    # Retrieve filepath of the ocr and manual transcription form the image filename
    txt_manual_file = "tmp"+os.sep+"extract_txt" + \
        os.sep+image_filename[:-4]+".gt.txt"
    txt_ocr_file = "tmp"+os.sep+"ocr_result" + \
        os.sep+image_filename[:-4]+"_ocr.txt"

    # We compare using lowercased string, the manual transcription will be lowercased when compared

    # Retrieve the manual transcription without tab and newline
    with open(txt_manual_file, newline='', encoding='UTF-8', errors="ignore") as inputfile:
        txt_manual = inputfile.readlines()
        txt_manual.pop()  # Remove last line which is autographe reference
        txt_manual = ''.join(txt_manual).replace('\t', '')

    # Retrieve the ocr prediction into a list of each segmented part
    with open(txt_ocr_file, newline='', encoding='UTF-8', errors="ignore") as inputfile:
        txt_ocr = inputfile.readlines()
        txt_ocr = [txt.replace('\t', '').replace(
            '\n', '').lower() for txt in txt_ocr]

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
    word_separator = [" ", ",", "", "\n"]

    new_upper = upper_bound
    new_lower = lower_bound
    character = corpus[new_lower]
    while character not in word_separator:
        new_lower -= 1
        character = corpus[new_lower]

    character = corpus[new_upper]
    while character not in word_separator:
        new_upper += 1
        if new_upper >= len(corpus):
            break
        character = corpus[new_upper]

    # Threshold check, to not extend too much
    if threshold >= 0:
        # should not complete more than threshold number of characters
        # if so, remove the incomplete word

        if lower_bound - new_lower >= threshold:
            new_lower = lower_bound
            character = corpus[new_lower]
            while character not in word_separator:
                new_lower += 1
                if new_lower >= len(corpus):
                    break
                character = corpus[new_lower]

        if new_upper - upper_bound >= threshold:
            new_upper = upper_bound
            character = corpus[new_upper]
            while character not in word_separator:
                new_upper -= 1
                character = corpus[new_upper]

    return corpus[new_lower+1:new_upper]


def check_dist_acceptance(x: int, dist: int):
    """
    Check whether the distance is smaller than the custom math function
    This math function was created as a separator between acceptable alignments and non-acceptable alignments

    Parameters:
        x : 
            Value x, corresponding the lenght of the OCR pattern
        dist : 
            Value y, minimal edit distance of the OCR pattern

    Returns:
        True if dist if smaller than the custom math function
    """
    if x < 0 or dist < 0:
        logger.warning(
            "It was asked to check the acceptance of a value that shouldn't be possible in a discrete environnement")
        return True

    if x >= 60 and dist < 0.6:
        return True
    elif x >= 20 and x <= 60 and dist < (0.005*x+0.3):
        return True
    elif x <= 20 and dist < (0.04*x-0.4):
        return True
    return False


@ timeit
def align_patterns(patterns: list, text: str, printing: bool = True) -> tuple:
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
    text = text.replace("\n", " ")

    # For each pattern found by the ocr
    # 1/ Align them in the original text using hamming distance
    #  (comppared in lowercase, because the poet tend the mix upper and lower case in writing)
    # 2/ With the best match, complete word if necessary
    for pattern in patterns:
        scores = []
        for i in range(len(text)-len(pattern)):
            scores.append(hamming_distance(
                pattern, text[i:i+len(pattern)].lower()))
        index = np.argmin(scores)

        # Complete words
        text_complete = complete_word(
            text, index, index+len(pattern), threshold=3)

        if not pattern or pattern.isspace():
            # Skip empty ocr/pattern
            pattern_index += 1
            continue

        # Get Word Error Rate and Character Error Rate
        wer, cer = calculate_error_rate(pattern, text_complete.lower())

        # Get the minimum between the hamming distance
        # and the CER = Levensthein distance with the text completed
        min_normalized = scores[index]/len(pattern)
        if min_normalized > cer:
            min_normalized = cer

        # Alignment to a smalll text is too much of a hazard
        if len(text_complete) > 15:

            # A distance too great is ignored
            if check_dist_acceptance(len(pattern), min_normalized):

                associations.append([
                    pattern, pattern_index, text_complete, scores[index]])
                indexes.append(index)

                # if True, if will log a trace of every alignment done ( cause a lot of logs )
                if printing:
                    logger.debug("For : "+str(pattern)+" | >> dist score : " +
                                 str(scores[index]/len(pattern)) + "\t\t\t at index : "+str(index))
                    logger.debug("\t "+text[index:index+len(pattern)])
                    logger.debug("\t "+text_complete)
                    logger.debug("WER : "+str(wer) +
                                 ", CER : "+str(cer))

        pattern_index += 1
    return associations, indexes


def get_usable_alignments(associations: dict, indexes: list) -> tuple:
    """
    Fodder function that do nothing for now,
    it could be used as an intermediary steps to clean up even more the alignments
    """
    return associations, indexes


def align_cropped(lst: list, indexes_origin: list, filepath: str) -> None:
    """
    For each alignment, create the pair text-image

    Parameters:
        lst:
            A list of curated [pattern, pattern_index, text_matched, distance_score]
        indexes_origin :
            List of indexes of every pattern in the original ocr prediction
            Unused in this function
        filepath:
            Path to the original image

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
    segmented_img_dir = "tmp"+os.sep+"segmented"

    indexes = [i[1] for i in lst]

    try:
        os.makedirs(segmented_img_dir, exist_ok=True)
        os.makedirs(cropping_dir, exist_ok=True)

        # Align text-image for crop
        img = cv.imread(filepath, cv.IMREAD_COLOR)
        img_segmented = img.copy()
        count_iterator = 0

        for i in range(len(predictions)):

            # Crop the image
            boundaries = predictions[i].line
            x_min = x_max = boundaries[0][0]
            y_min = y_max = boundaries[0][1]
            for j in range(1, len(boundaries)):

                # If segment is used, draw it in blue
                if i in indexes:
                    img_segmented = cv.line(img_segmented, boundaries[j-1],
                                            boundaries[j], (255, 0, 0, 0.25), 5)
                else:  # draw it in red

                    img_segmented = cv.line(img_segmented, boundaries[j-1],
                                            boundaries[j], (0, 0, 255, 0.25), 5)

                x = boundaries[j][0]
                y = boundaries[j][1]

                # Take larger coordinates for a rectangle cropping
                x_min = (x if x < x_min else x_min)
                x_max = (x if x > x_max else x_max)
                y_min = (y if y < y_min else y_min)
                y_max = (y if y > y_max else y_max)

            # If the text matched is empty, skip

            # If the segment width isn't at least 20% of the total image width, skip (most likely noise)
            # Also re-draw them in orange (less visible)
            if (x_max-x_min) < 0.2*img.shape[1]:

                boundaries = predictions[i].line
                for j in range(1, len(boundaries)):

                    img_segmented = cv.line(img_segmented, boundaries[j-1],
                                            boundaries[j], (80, 165, 255, 1), 5)
                continue
            if i not in indexes:
                continue

            # Create cropped file associated
            cropped = img[y_min:y_max, x_min:x_max]

            # new filepath,  also remove additionnal "." = dots due to kraken/ketos implementation
            cropped_img_path = cropping_dir+os.sep + \
                filename[:-4].replace(".", "")+"_"+str(count_iterator)+".jpg"
            cv.imwrite(cropped_img_path, cropped)

            # Create txt file associated
            with open(cropped_img_path[:-4]+'.gt.txt', 'w', encoding='UTF-8', errors="ignore") as f:
                f.write(lst[count_iterator][2])
            count_iterator += 1
        logger.debug("Finished cropping " +
                     str(count_iterator) + " times for "+filename)

        # Save the original image with segmentation drawn on it
        cv.imwrite(segmented_img_dir+os.sep +
                   filename[:-4]+"_segmented.jpg", img_segmented)

    except KeyboardInterrupt:
        # If this process is interrupted, considering we use the presence of the folder
        # to indicate files are already processed, we remove the folder unfinished
        shutil.rmtree(cropping_dir)
        exit()


@ timeit
def batch_align_crop(image_dir: str, printing: bool = False) -> None:
    """
    Batch process image files to create pairs of alignments text-images

    Parameters:
        image_dir:
            Directory where images are located
        printing:
            If True, logger will log in debug of each text-image alignment with their score

    Returns:
        None
    """
    logger.info("Started batch align text-images with segmented images")
    count = 0
    # Process the entire directory
    for (dirpath, subdirnames, filenames) in os.walk(image_dir):
        for filename in filenames:

            # Skip non image file
            if not filename.lower().endswith(image_extension):
                continue

            filepath = dirpath+os.sep+filename
            # Process the entire directory, thism ay cause error due to image present but not yet ocr-ed
            count = apply_align(
                count, filename, filepath, len(filenames), printing=printing)


def apply_align(count: int, filename: str, filepath: str, total: int, printing: bool = False) -> int:
    """
    Apply alignment to create pairs of text-images

    Parameters:
        count:
            Current count of images aligned (for statistic purpose)
        filename :
            Name of the image file
        filepath :
            Path to the image file
        total :
            Total number of alignment (for statistic purpose)
        printing : 
            If True, logger will log in debug of each text-image alignment with their score

    Returns:
        count + 1
    """

    # Check if folder for cropped image is already present, if yes it means the file was already aligned
    if os.path.exists("tmp"+os.sep+"cropped_match"+os.sep + filename):
        return count

    logger.info("Align " + filepath + " " + str(count)+"/"+str(total))
    # Fetch the manual transcription and the ocr
    try:
        txt_manual, txt_ocr = txt_compare_open(filename)
    except Exception as Argument:
        logger.warning("Error loading text for alignment : "+str(Argument))
        return count

    # Align each pattern of the ocr to the transcription
    associations, indexes = align_patterns(
        txt_ocr, txt_manual, printing=printing)

    # Does nothing as of now
    # When implemented will curate the alignments
    lst_alignments_usable, index_used = get_usable_alignments(
        associations, indexes)

    # Crop and produce every pair of text-image
    align_cropped(lst_alignments_usable, index_used,  filepath)

    count += 1
    logger.debug("Cropped a total of "+str(count)+" images")
    return count


if __name__ == "__main__":

    main_dir = "tmp/extract_image"

    batch_align_crop(main_dir)
