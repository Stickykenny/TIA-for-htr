"""
This file launch a webpage to manually align, for the purpose of improving the dataset before training

Usage : add_align.py [number_to_align] [number_to_skip]
        After manually aligned, move the downloaded json into the manual_align/ and relaunch this file to clean the alignments

Arguments:
    number_to_align           Number of image to align/ to generate web page
    number_to_skip            Number of image to skip (i.e. skip the ten first who were already algined).

Exemple of the steps to take:
    > align.py 10
    > <Manually align using each generated web page>
    > <Move the 10 produced/downloaded json into manual_align/>  
    > align.py 10 (= relaunch the same command )
    > Now will only remain pairs of text/image and the json

    You can increase the number to your convenience
"""

import os
import ujson
from PIL import Image
import re
import sys


def remove_additionnal_dots(txt: str):
    """
    Will remove all dots not considered extension related for jpg,png and gt.txt files

    Parameters:
        txt : 
            Text to curate

    Returns:
        Curated txt
    """
    if txt.endswith((".jpg", ".png")):
        return ''.join(txt[:-4].split("."))+".jpg"
    if txt.endswith(".gt.txt"):
        return ''.join(txt[:-7].split("."))+".gt.txt"
    return txt


def generate_manual_align_webpage(title: str, images: list, text_ref: str, total: int, aligned: int) -> None:
    """
    Will generate the webpage for manual alignment text/image

    Parameters:
        title : 
            Also referred as the image filename
        images :
            List of all the cropped images of the title image
        text_ref :
            Transcription of the image
        total : 
            Total number of cropped image

    Returns:
        None 
    """
    with open("ressources"+os.sep+"manual_align.html", "r", encoding="UTF-8", errors="ignore") as base_html:
        webpage = base_html.read()

    os.makedirs("manual_align"+os.sep+title, exist_ok=True)

    # Replace add <span> tag to every spaces and breakline
    text_ref = "<span class='click_text'>_</span>"+text_ref.replace(
        " ", "<span class='click_text'> </span>").replace("\n", "<span class='click_text'>_</span><br><span class='click_text'>_</span>")+"<span class='click_text'> </span>"

    # Insert dynamic data into the base webpage

    images = [img.replace("manual_align"+os.sep, "") for img in images]
    webpage = webpage.replace("SOURCE_TEXT", text_ref)
    webpage = webpage.replace("TITLE", title)
    webpage = webpage.replace("COMMENT", "This page originally already was " +
                              str(aligned)+"/"+str(total) + " cropped aligned")
    webpage = webpage.replace("IMAGELIST", str(images))
    webpage = webpage.replace("TOTALCROP", str(total))
    webpage = webpage.replace(
        "FULLIMAGE", "tmp"+os.sep+"segmented"+os.sep+title[:-4]+"_segmented.jpg")
    webpage = webpage.replace(
        "manual_align.css", ".."+os.sep+"ressources"+os.sep+"manual_align.css")

    with open("manual_align"+os.sep+title+".html", "w", encoding="UTF-8", errors="ignore") as new_html:
        new_html.write(webpage)


def retrieve_transcription(filename: str) -> str:
    """
    Retrieve the transcription of the image file

    Parameters:
        filename : 
            Image filename

    Returns:
        The transcription of the image
    """
    name_pattern = re.compile("\d+(?:-\d+)*")
    # cote = name_pattern.search(filename).group(0)

    # Retrieve filepath of the ocr and manual transcription form the image filename
    txt_manual_file = "tmp"+os.sep+"extract_txt"+os.sep+filename[:-4]+".gt.txt"

    # Retrieve the manual transcription without tab and newline
    with open(txt_manual_file, newline='', encoding='UTF-8', errors="ignore") as inputfile:
        txt_manual = inputfile.readlines()
        txt_manual = ''.join(txt_manual).replace('\t', '')
    return txt_manual


def curate_alignments(acceptlist: list, filename: str, order: bool = False) -> None:
    """
    Remove cropped image without transcription, and create txt file for the one aligned

    Parameters:
        acceptlist : 
            List of cropped image acceptation
            [ O/1 , "transcription" ]
        filename :
            Name of the image file concerned
        order : 
            If True, files will be sorted in alphabetical order before being curated
            (for the implementation with google Lens)

    Returns:
        None 
    """

    for cropped_dir, subfolders, files in os.walk("manual_align"+os.sep+filename):

        # order is for the google lens usage implementation
        # where files have lost their position meaning and are found using their alphabetical order
        if order:
            files = sorted(files)

        for file in files:
            if file.endswith(".gt.txt"):
                continue
            crop_count = int(file.split("_")[-1][:-4])
            # Remove cropped image with no transcription
            if acceptlist[crop_count][0] == 0:
                os.remove("manual_align"+os.sep+filename+os.sep+file)
            # Create the text file associated
            else:
                txt_filename = remove_additionnal_dots(file[:-4]+".gt.txt")
                with open("manual_align"+os.sep+filename+os.sep+txt_filename, 'w', encoding="UTF-8", errors="ignore") as newtxt:
                    newtxt.write(acceptlist[crop_count][1])

                os.rename(cropped_dir+os.sep+file, cropped_dir +
                          os.sep+remove_additionnal_dots(file))

    print("Folder tmp"+os.sep+filename+" is curated.")


def generate_manual_alignments(number: int = -1, skip: int = 0) -> None:
    """
    Will generate n numbers of webpage for manual alignments

    Parameters:
        number : 
            Number of webpage to generate

    Returns:
        None 
    """

    # Get last monitoring data
    segment_stats_path = "tmp"+os.sep+"save"+os.sep+"segment_stats"
    segments_path = "tmp"+os.sep+"save"+os.sep+"segment"
    files = sorted(
        list(next(os.walk(segment_stats_path)))[2])
    # The last saved monitoring json is the last of half the file, due to the half being the histogram images
    last_json = files[(len(files)//2-1)]
    with open(segment_stats_path+os.sep+last_json, "r", encoding="UTF-8", errors='ignore') as stats_file:
        segment_stats = ujson.load(stats_file)[1]
    # Skip image that have too few images (=noises detected) plus a set number of skip in argument
    skip_count = 0
    while segment_stats[skip_count][4] < 5 and segment_stats[skip_count][1] == 0:
        skip_count += 1

    total_skip = skip_count+skip if skip_count + \
        skip < len(segment_stats) else len(segment_stats)
    segment_stats = segment_stats[total_skip:]

    if number > -1:
        number = len(segment_stats) if number + \
            total_skip > len(segment_stats) else number+total_skip
        segment_stats = segment_stats[total_skip:number]
    print("Look for images up to the number "+str(number))

    progress_count = 0
    for cropped_path, usage_ratio, used, total, usable in segment_stats:
        filename = cropped_path.split(os.sep)[-1]
        images = []

        # If a list of curated cropped already exist skip
        acceptlist_path = "manual_align"+os.sep+filename[:-4]+".json"
        if os.path.exists(acceptlist_path):
            with open(acceptlist_path, "r", encoding="UTF-8", errors='ignore') as segment_file:
                acceptlist = ujson.load(segment_file)
                curate_alignments(acceptlist, filename)
        else:

            os.makedirs("manual_align"+os.sep+filename, exist_ok=True)
            # Load segmentation data
            img = Image.open("tmp"+os.sep+"extract_image"+os.sep+filename)
            width = img.width
            with open(segments_path+os.sep+filename+"_segment.json", "r", encoding="UTF-8", errors='ignore') as segment_file:
                segments = ujson.load(segment_file)

            # Prepare the cropped images for the manual alignments
            crop_count = 0
            name_count = 0
            for segment in segments["lines"]:
                boundaries = segment["boundary"]
                x_min = x_max = boundaries[0][0]
                y_min = y_max = boundaries[0][1]
                for i in range(1, len(boundaries)):

                    x = boundaries[i][0]
                    y = boundaries[i][1]

                    # Take larger coordinates for a rectangle cropping
                    x_min = (x if x < x_min else x_min)
                    x_max = (x if x > x_max else x_max)
                    y_min = (y if y < y_min else y_min)
                    y_max = (y if y > y_max else y_max)

                cropped = img.crop((x_min, y_min, x_max, y_max))
                w, h = cropped.size

                # Skip images that are too 'small'
                if w < 0.2*width:
                    name_count += 1
                    continue
                cropped_name = "manual_align"+os.sep+filename + \
                    os.sep+filename+"_"+str(crop_count)+".jpg"
                images.append(cropped_name)
                cropped.save(cropped_name)
                crop_count += 1
                name_count += 1

            # If no crop can be manually aligned skip
            if crop_count == 0:
                os.removedirs("manual_align"+os.sep+filename)
                continue
            img.close()

            text_ref = retrieve_transcription(filename)
            generate_manual_align_webpage(
                filename, images, text_ref, usable, used)
            progress_count += 1
            print("Generated "+str(progress_count)+"/" +
                  str(len(segment_stats))+" manual align webpage")


if __name__ == '__main__':

    number_to_align = 10
    number_to_skip = 0
    try:
        if len(sys.argv) > 1:
            number_to_align = int(sys.argv[1])
            if len(sys.argv) > 2:
                number_to_skip = int(sys.argv[2])
    except:
        print(__doc__)
        sys.exit()

    generate_manual_alignments(number_to_align, number_to_skip)
