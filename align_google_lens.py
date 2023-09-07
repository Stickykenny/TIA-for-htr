
import align
import os
import shutil
from add_align import curate_alignments


def init_glens_addon():
    tmp_folder = "glens"+os.sep+"juxta_tmp"

    os.makedirs(tmp_folder, exist_ok=True)

    checker = os.listdir(tmp_folder)

    # If no file is found in glens/juxta_tmp
    # It will bring out one image for the user to upload to Google Lens
    if not checker:
        files = [file for file in os.listdir("juxtaposed") if os.path.isfile(
            os.path.join("juxtaposed", file))]

        selected_file = os.path.join("juxtaposed", files[0])

        shutil.move(selected_file, tmp_folder)
        print("Check here : " + tmp_folder)
        print(" Image file to process in Google Lens : " + files[0])
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
    unprocessed_ocr = """mdvocr Bond ja trouve. à semplis me drission.
mdvocr aurons pé devance, plus il nous dédommagera
mdvocr honde le Notre sera be tout les Mondes
mdvocrvore vingt-cing francs, ne pouvant ton
mdvocr envir diventage. "Il y a toughers quely mdvocr grave pour anster l'élan de mon Ahne.
mdvocrois, m-ce pas ? Na! vela oss! as to je
mdvocrit pas pourre
mdvocr tu te la Serais par
mdvocr je Torre tas moins avec l'affection d'iene
mdvocr Bonne at tendre Soccer, et au Nom de
mdvocr mon Mari
mdvocrewis acine et charchal are Milien de toute nos
mdvocr to fivile amed.
mdvocr chosceline Valmore un
mdvocr épreuve j'ai des momend
mais
mdvocr me end to yours soutenue par cette main Fevine
mdvocr mdvocr nous déver, mon Bon Jely to air qual
mdvocracia davoir également sempli la timme
mdvocren minout to element, the mas Bien vivent
mdvocr consolé des amitier légèren et oubliender de""".replace("\n", " ")
    return unprocessed_ocr
    print("Enter/Paste your content. Ctrl-D or Ctrl-Z ( windows ) to save it.")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        contents.append(line)

    unprocessed_ocr = " ".join(contents)
    return unprocessed_ocr


def generate_web_alignment_selector(result, file):

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
    for i in range(len(result)):

        # Wrapper with an id
        html_code += '<div class="wrapper selected" id="' + \
            images[result[i][1]-1]+'">'

        # Image on the left
        html_code += '<div class="row left"><img id="'+images[result[i][1]-1]+'"  src="' + \
            ".."+os.sep + ".."+os.sep + \
            images[result[i][1]-1]+'" alt="' + \
            images[result[i][1]-1]+'" ></div>'
        index_used.append(result[i][1]-1)

        # OCR and Transcription aligned on the right
        html_code += '<div class="row right"><p> <input type="text" class="valueSelected" value="' + \
            str(result[i][2]) + '" originalValue="'+str(result[i][2])+'" size="50" ><br><referenceText class="referenceText">' + \
            str(result[i][0])+'</referenceText><br></p></div>'

        html_code += "</div>"

    # Additional image cropped that couldn't find a correct alignment
    for i in range(len(images)):
        if i not in index_used:
            html_code += '<div class="wrapper unselected" id="' + \
                images[i]+'">'

            html_code += '<div class="row left"><img id="'+images[i]+'"  src="' + \
                ".."+os.sep + ".."+os.sep + \
                images[i]+'" alt="' + \
                images[i]+'" ></div>'

            html_code += '<div class="row right"><p> <input type="text" class="valueSelected" originalValue="' + \
                '" size="50" ><br><referenceText class="referenceText">' + \
                "No correct alignment was found" + \
                '</referenceText><br>' + '</p></div>'

            html_code += "</div>"

    html_code += '</div>'

    # Fill in the template
    webpage = webpage.replace("CONTENT", html_code)
    webpage = webpage.replace("TOTALCROP", str(len(images)))
    webpage = webpage.replace("TITLE", file)

    # Create the webpage file
    with open(user_folder+os.sep+file.replace('.jpg', '.html'), "w", encoding="UTF-8", errors="ignore") as new_page:
        new_page.write(webpage)


def retrieve_patterns(file):
    ocr_result_folder = "glens"+os.sep+"ocr_result"
    done_folder = "glens"+os.sep+"juxta_done"

    os.makedirs(done_folder, exist_ok=True)
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
