"""
This file is similar to add_align.py in purpose but with Google Lens
This file will single out a juxtaposed image for it to be OCRed by Google Lens,
Then after the used entered the OCR result, a webpage will be created for the user to accept and correct the alignments

Usage : align_google_lens.py

Exemple of the steps to take:
    > align_google_lens.py    ( It single out a juxtaposed image )
    > <Use Google Lens on the image at glens/juxta_tmp>
    > align_google_lens.py
    > <Paste the OCR result from Google Lens, the program will generate a webpage at glens/choose_align>
    > <Accept and correct the alignments, validate it then move the json produced/downloaded to manual_align/ >
    > align_google_lens.py (It will curate the concerned image folder using the json and restart the process)

"""

import align
import os
import shutil
from add_align import curate_alignments
import ujson


def init_glens_addon():
    """
    Proceed to single out a juxtaposed image, also curate if json were produced and moved to concerned folder

    Returns:
        The filename that will be processed
    """
    tmp_folder = "glens"+os.sep+"juxta_tmp"
    done_folder = "glens"+os.sep+"juxta_done"

    os.makedirs(done_folder, exist_ok=True)
    os.makedirs(tmp_folder, exist_ok=True)

    checker = os.listdir(tmp_folder)

    # Check for the existence of a JSON in manual_align/ meaning the file was already done,
    # so we can go into the next juxtaposed image to prepare
    if checker:
        json_filename = checker[0].replace("_juxtaposed.jpg", ".json")
        json_path = "manual_align"+os.sep+json_filename
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="UTF-8", errors='ignore') as segment_file:
                acceptlist = ujson.load(segment_file)
                filename = json_filename.replace(".json", ".jpg")
                curate_alignments(acceptlist, filename, order=True)

            # Clean and moved used files (juxtaposed used, selector webpage)
            shutil.move(tmp_folder+os.sep +
                        checker[0], done_folder+os.sep+checker[0])
            html_file = filename.replace(".jpg", ".html")
            shutil.move("glens"+os.sep+"choose_align"+os.sep +
                        html_file, done_folder+os.sep+html_file)

    # If no file is found in glens/juxta_tmp
    # It will bring out one image for the user to upload to Google Lens
    if not checker:
        files = [file for file in os.listdir("juxtaposed") if os.path.isfile(
            os.path.join("juxtaposed", file))]

        selected_file = os.path.join("juxtaposed", files[0])

        shutil.move(selected_file, tmp_folder)
        print("Check here : " + tmp_folder)
        print(
            " Image file to process in Google Lens (Copy full text OCR and paste in terminal/console): " + files[0])
        exit()

    # Else
    file_juxta = checker[0]  # filename_juxtaposed.jpg
    file = file_juxta.replace("_juxtaposed", "")   # filename.jpg

    return file


def retrieve_multiline_text() -> str:
    """
    Ask the user to enter the OCR result

    Returns :
        The OCR result in one line
    """
    print("Enter/Paste your content.\n Use Ctrl-D or Ctrl-Z ( windows ) to save it.")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        contents.append(line)

    unprocessed_ocr = " ".join(contents)
    return unprocessed_ocr


def generate_web_alignment_selector(result: list, file: str) -> None:
    """
    Generate the webpage for that for selecting and correcting alignments

    Parameters:
        result :
            Results of the algorithmic alignments, the results are obtained with align.align_patterns()
        file :
            Filename of the image concerned

    Returns:
        None
    """
    user_folder = "glens"+os.sep+"choose_align"
    os.makedirs(user_folder, exist_ok=True)

    # We will follow the alphabetical order for referencing images
    images = ["manual_align"+os.sep+file+os.sep +
              f for f in sorted(os.listdir("manual_align"+os.sep+file))]

    result = sorted(result, key=lambda x: str(x[1]))

    # Create the webpage

    # Open the template
    with open("ressources"+os.sep+"semialign_select.html", "r", encoding="UTF-8", errors="ignore") as base_html:
        webpage = base_html.read()

    # Generate the content
    html_code = '<div id="top" style="text-align: center">'
    index_used = []  # List of all images index index, we then use it to know which image didn't find an alignment
    # For every pattern align a row with image on the left and transcription on the right

    reorder_div = []  # Used for re-ordering the div in their filename alphabetical order

    # Image cropped that have found an alignment
    for i in range(len(result)):

        # Wrapper with an id
        divbox = '<div class="wrapper selected" id="' + \
            images[result[i][1]-1]+'">'

        # Image on the left
        divbox += '<div class="row left"><img id="'+images[result[i][1]-1]+'"  src="' + \
            ".."+os.sep + ".."+os.sep + \
            images[result[i][1]-1]+'" alt="' + \
            images[result[i][1]-1]+'" ></div>'
        index_used.append(result[i][1]-1)

        # OCR and Transcription aligned on the right
        divbox += '<div class="row right"><p> <input type="text" class="valueSelected" value="' + \
            str(result[i][2]) + '" originalValue="'+str(result[i][2])+'" size="50" ><br><referenceText class="referenceText">' + \
            str(result[i][0])+'</referenceText><br></p></div>'

        divbox += "</div>"
        reorder_div.append([divbox, images[result[i][1]-1]])

    # Additional image cropped that couldn't find a correct alignment,
    for i in range(len(images)):
        if i not in index_used:
            divbox = '<div class="wrapper unselected" id="' + \
                images[i]+'">'

            divbox += '<div class="row left"><img id="'+images[i]+'"  src="' + \
                ".."+os.sep + ".."+os.sep + \
                images[i]+'" alt="' + \
                images[i]+'" ></div>'

            divbox += '<div class="row right"><p> <input type="text" class="valueSelected" originalValue="' + \
                '" size="50" ><br><referenceText class="referenceText">' + \
                "No correct alignment was found" + \
                '</referenceText><br>' + '</p></div>'

            divbox += "</div>"
            reorder_div.append([divbox, images[i]])

    # We reorder to fit alphabetical order
    reorder_div = sorted(reorder_div, key=lambda x: x[1])

    for divbox in reorder_div:
        html_code += divbox[0]

    html_code += '</div>'

    # Fill in the template
    webpage = webpage.replace("CONTENT", html_code)
    webpage = webpage.replace("TOTALCROP", str(len(images)))
    webpage = webpage.replace("TITLE", file)

    # Create the webpage file
    webpage_filepath = user_folder+os.sep+file.replace('.jpg', '.html')
    with open(webpage_filepath, "w", encoding="UTF-8", errors="ignore") as new_page:
        new_page.write(webpage)

    print("  -------  ")

    print("Alignment selector was generated. Use "+webpage_filepath +
          " to produce a JSON indicating which alignment are accepted.")


def retrieve_patterns(file: str) -> str:
    """
    Retrieve patterns, by asking the user result of the OCR from Google Lens

    Parameters:
        file : 
            Filename of the image concerned

    Returns:
        List of the pattern predicted by the OCR
    """
    ocr_result_folder = "glens"+os.sep+"ocr_result"
    os.makedirs(ocr_result_folder, exist_ok=True)

    # This instruction will require user action to paste into the dialog box the result of Google Lens OCR
    unprocessed_ocr = retrieve_multiline_text()

    # Save Google Lens Result
    with open(ocr_result_folder+os.sep+file.replace(".jpg", ".gt.txt"), "w", encoding="UTF-8", errors="ignore") as ocr_write_file:
        ocr_write_file.write(unprocessed_ocr)

    # Separate the pattern using "mdvocr"
    unprocessed_ocr_patterns = unprocessed_ocr.lower().replace("\n", " ").split("mdvocr")

    return unprocessed_ocr_patterns


if __name__ == "__main__":

    # This instruction can stop the program
    # It decide the mode the program will be in
    selected_file = init_glens_addon()

    ocr_patterns = retrieve_patterns(selected_file)

    # Retrieve the original transcriptions
    with open("tmp"+os.sep+"extract_txt"+os.sep+selected_file[:-4]+'.gt.txt', "r", encoding="UTF-8", errors="ignore") as ref_file:
        text_reference = ref_file.read()

    result, used_pattern_index = align.align_patterns(
        ocr_patterns, text_reference)

    generate_web_alignment_selector(result, selected_file)
