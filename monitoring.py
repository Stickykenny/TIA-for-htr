"""
monitoring.py: Contains functions for monitoring and logging performance/time
"""

import matplotlib.pyplot as plt
import time
import logging
from datetime import datetime
import os
from PIL import Image
import ujson
logger = logging.getLogger("TIA_logger")
image_extension = (".jpg", ".png")


def setup_logger():
    """
    Setup the default logger

    Returns :
        The logger
    """

    os.makedirs("logs", exist_ok=True)

    # Set parameters and default values of logger
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create a File Handler to log into a file
    filename = "logs"+os.sep + datetime.now().strftime('logs_%Y_%m_%d_%H_%M.log')
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)

    # Create a Stream Handler for stream's output on console
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def timeit(f):
    """
    Decorator used for timing runtime of a function, it logs them using the logger

    Parameters :
        f :
            Function to monitor

    Returns :
        Result of the function
    """
    def timed(*args, **kw):
        # Start the timer
        ts = time.time()

        logger.debug("")
        logger.debug("\t>> Starting timer for %r() <<" % (f.__name__))

        result = f(*args, **kw)  # Apply the function

        # End the timer
        te = time.time()
        logger.debug("\t>> Time taken for %r() : %.6f sec <<" %
                     (f.__name__, te-ts))
        logger.debug("")

        return result
    return timed


def generate_compare_html(source_dir: str) -> None:
    """
    Generate html page of index and comparison page for pairs of text/image

    Parameters :
        source_dir :
            Path where folders of cropping are located

    Returns :
        None
    """

    # Prepare Folders
    previews_path = "tmp"+os.sep+"cropping_preview"
    os.makedirs(previews_path, exist_ok=True)

    # html_index is the html page indexing the others html page of cropping
    with open("tmp"+os.sep+"cropping_preview_index.html", 'w', encoding='UTF-8', errors="ignore") as html_index:

        # Write the beginning of the html_index
        html_index.write('''<!DOCTYPE html>
                        <html lang="en">
                        <head>
                        <meta charset="UTF-8">
                        <title>Index of all cropping done next to their text aligned</title>
                        </head>
                        <body><ul>''')

        # For every cropping folder
        # Showcase all their text/image alignments in a cropping html page
        for directory, subfolders, files in sorted(os.walk(source_dir))[1:]:
            image_cropping_preview = previews_path + \
                os.sep+directory.split(os.sep)[-1]+".html"
            with open(image_cropping_preview, 'w', encoding='UTF-8', errors="ignore") as cropping_html:

                # Write the header of the file
                cropping_html.write('''<!DOCTYPE html>
                            <html lang="en">
                            <head>
                            <meta charset="UTF-8">''')
                # Have the title be the path to the cropped images
                cropping_html.write(
                    '<title>'+os.sep.join(image_cropping_preview.split(os.sep)) + " cropped" + '</title>')
                # Add a script to toggle show/hide cropping of a folder
                cropping_html.write('''<script >
                                    function toggleVisibility(contentId) {
                                    var content = document.getElementById(contentId);
                                    content.style.display = (content.style.display == 'none') ? 'block': 'none';}
                            </script >
                            </head >
                            <body >''')
                cropping_html.write('<br><div style="text-align:center;"><button onclick = "toggleVisibility(\'' +
                                    directory+'\')" > <h1 > '+directory+' </button ></div>')
                cropping_html.write(
                    '<div style="text-align:center;  display:block;" id="'+directory+'">')

                # Introduce every crop and their text into the html page
                cropping_count = 0
                for file in files:

                    # Skip non image file, should be jpg, due to previous implementation see align.py
                    if not file.endswith('.jpg'):
                        continue
                    image_path = directory+os.sep+file
                    cropping_html.write('<img style="min-width:500px;max-width:1000px"  src="' + ".."+os.sep + ".."+os.sep +
                                        image_path+'" alt="'+image_path+'" >')

                    # Retrieve the text aligned
                    text_filename = ''.join(file.split(".")[:-1])+".gt.txt"
                    with open(directory+os.sep+text_filename, 'r', encoding='UTF-8', errors="ignore") as text_file:
                        text_aligned = text_file.readline()
                        cropping_html.write('<p>'+text_aligned+'</p>')
                    cropping_count += 1

                # End the html tags of the croppping html page
                cropping_html.write('</div></body>')

            # Add an index into the main html_index page
            href = os.sep.join(image_cropping_preview.split(os.sep)[1:])
            html_index.write('<li>  <a href="'+href+'">' +
                             href + ', '+str(cropping_count)+' cropping</a>   </li>')
            cropping_count = 0

        # End the html tags of the html_index page
        html_index.write("</ul></body>")


def quantify_segment_used(image_dir: str, cropped_dir: str, segment_dir: str) -> None:
    """
    Generate an histogram of the distribution of segment usage

    Parameters :
        image_dir :
            Path to the directory with images
        cropped_dir :
            Path to the directory with the cropping
        segment_dit :
            Path to the directory with the segment data
    Returns :
        None
    """
    os.makedirs("tmp"+os.sep+"save"+os.sep + "segment_stats", exist_ok=True)

    date = datetime.now().strftime('_%Y_%m_%d_%H_%M')
    data = []
    percents_used = []
    images_data = []

    # For every image in the image_dir find their cropping_dir
    # Count the number of pairs in this folder to create data
    for maindir, _, images in list(os.walk(image_dir)):

        for image in images:
            if not image.lower().endswith(image_extension):
                continue
            segment_used = 0
            directory = cropped_dir+os.sep+image
            if not os.path.exists(cropped_dir+os.sep+image):
                cropped_in_dir = 0
            else:
                for _, _, files in os.walk(directory):

                    # Divided by 2, because half of the files are the text transcription
                    cropped_in_dir = len(files)//2

            path_to_segment_data = os.path.join(
                segment_dir, os.path.relpath(directory,
                                             cropped_dir)+"_segment.json")
            with open(path_to_segment_data, "r", encoding="UTF-8", errors="ignore") as segment_file:
                segment_data = ujson.load(segment_file)

            nb_segments = len(segment_data["lines"])
            if nb_segments == 0:
                logger.info(
                    "Ignored image with no segmentation detected : "+directory)
                continue
            percents_used.append(cropped_in_dir/nb_segments)

            # Get number of segment having a width that is more than 20% of the image's width
            PIL_image = Image.open(maindir+os.sep+image)
            image_width = PIL_image.width
            PIL_image.close()

            for segment in segment_data["lines"]:
                baseline = segment["baseline"]
                x_min = x_max = baseline[0][0]
                for i in range(1, len(baseline)):

                    x = baseline[i][0]

                    # Take larger coordinates for a rectangle cropping
                    x_min = (x if x < x_min else x_min)
                    x_max = (x if x > x_max else x_max)

                cropped_width = x_max - x_min
                if cropped_width > 0.2*image_width:
                    segment_used += 1

            # Saves information : [ Image filedir, percent of segment used , number of cropped aligned, number total segment, number of cropped_width> 20% image_width ]
            images_data.append(
                [directory, cropped_in_dir/nb_segments, cropped_in_dir, nb_segments, segment_used])

    # Create histogram
    plt.figure(figsize=(10, 5))
    plt.hist(percents_used, bins=100, orientation='horizontal')
    plt.title('Distribution of segmentation usage in cropping', fontsize=16)
    plt.xlabel('Number of images', fontsize=12)
    plt.ylabel('Percentage of segments used', fontsize=12)
    plt.savefig("tmp"+os.sep+"save"+os.sep + "segment_stats"+os.sep +
                "distribution_segment_usage"+date+".jpg")

    # Save histogram's data
    data.extend([sorted(percents_used), sorted(
        images_data, key=lambda x:(x[1], x[4]))])
    with open("tmp"+os.sep+"save"+os.sep+"segment_stats"+os.sep+"distribution_datas"+date+".json", "w", encoding="UTF-8", errors="ignore") as new_json:
        ujson.dump(data, new_json, indent=4)
