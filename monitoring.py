"""
monitoring.py: Contains functions for monitoring and logging performance/time
"""

import time
import logging
from datetime import datetime
import os
logger = logging.getLogger("TIA_logger")


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
        for dir, subfolders, files in sorted(os.walk(source_dir))[1:]:
            image_cropping_preview = previews_path + \
                os.sep+dir.split(os.sep)[-1]+".html"
            with open(image_cropping_preview, 'w', encoding='UTF-8', errors="ignore") as cropping_html:

                # Write the base of the file
                cropping_html.write('''<!DOCTYPE html>
                            <html lang="en">
                            <head>
                            <meta charset="UTF-8">''')
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
                                    dir+'\')" > <h1 > '+dir+' </button ></div>')
                cropping_html.write(
                    '<div style="text-align:center;  display:block;" id="'+dir+'">')

                # Introduce every crop and their text into the html page
                cropping_count = 0
                for file in files:

                    # Skip non image file, should be jpg, due to previous implementation see align.py
                    if not file.endswith('.jpg'):
                        continue
                    image_path = dir+os.sep+file
                    cropping_html.write('<img style="min-width:500px;max-width:1000px"  src="' + ".."+os.sep + ".."+os.sep +
                                        image_path+'" alt="'+image_path+'" >')

                    # Retrieve the text aligned
                    text_filename = ''.join(file.split(".")[:-1])+".gt.txt"
                    with open(dir+os.sep+text_filename, 'r', encoding='UTF-8', errors="ignore") as text_file:
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


if __name__ == "__main__":

    cropped_dir = "tmp"+os.sep+"cropped_match"

    generate_compare_html(cropped_dir)
