"""
This file launch a webpage to manually align, for the purpose of improving the dataset before training
"""
import os
import ujson
from PIL import Image
import re


def generate_manual_align_webpage(title: str, images: list, text_ref: str , total:int) -> None:
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
    with open("ressources"+os.sep+"manual_align.html", "r", encoding="UTF-8", errors="ignore") as base_html :
        webpage = base_html.read()

    os.makedirs("manual_align"+os.sep+title, exist_ok=True)

    # Replace add <span> tag to every spaces and breakline
    text_ref = "<span class='click_text'>_</span>"+text_ref.replace(
        " ", "<span class='click_text'> </span>").replace("\n", "<span class='click_text'>_</span><br><span class='click_text'>_</span>")+"<span class='click_text'> </span>"

    # Insert dynamic data into the base webpage

    images = [img.replace("manual_align"+os.sep, "") for img in images]
    webpage = webpage.replace("SOURCE_TEXT", text_ref)
    webpage = webpage.replace("TITLE", title)
    webpage = webpage.replace("IMAGELIST", str(images) )
    webpage = webpage.replace("TOTALCROP", str(total) )
    webpage = webpage.replace("manual_align.css", ".."+os.sep+"ressources"+os.sep+"manual_align.css" )


    with open("manual_align"+os.sep+title+".html", "w", encoding="UTF-8", errors="ignore") as new_html :
        new_html.write(webpage)

def retrieve_transcription(filename:str) ->str:
    """
    Retrieve the transcription of the image file

    Parameters:
        filename : 
            Image filename

    Returns:
        The transcription of the image
    """
    name_pattern = re.compile("\d+(?:-\d+)*")
    cote = name_pattern.search(filename).group(0)

    # Retrieve filepath of the ocr and manual transcription form the image filename
    txt_manual_file = "tmp"+os.sep+"extract_txt"+os.sep+cote+".gt.txt"

    # Retrieve the manual transcription without tab and newline
    with open(txt_manual_file, newline='', encoding='UTF-8', errors="ignore") as inputfile:
        txt_manual = inputfile.readlines()
        txt_manual = ''.join(txt_manual).replace('\t', '')
    return txt_manual


def generate_manual_alignments(number:int=-1) -> None :
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
    os.makedirs("manual_alignments",exist_ok=True)
    files = sorted(
        list(next(os.walk(segment_stats_path)))[2])
    # The last saved monitoring json is the last of half the file, due to the half being the histogram images
    last_json = files[(len(files)//2-1)]
    with open(segment_stats_path+os.sep+last_json, "r", encoding="UTF-8", errors='ignore') as stats_file:
        segment_stats = ujson.load(stats_file)[1]

    # Skip image that have too few images (=noises detected)
    skip_count= 0
    while segment_stats[skip_count][4] < 5 and segment_stats[skip_count][1] == 0 :
        skip_count+=1

    if number > -1 :
        number = len(segment_stats) if number+skip_count > len(segment_stats) else number+skip_count
        segment_stats = segment_stats[skip_count:number]
    print("Look for images up to the number "+str(number))

    for cropped_path, usage_ratio, used, total, usable in segment_stats : 
        filename= cropped_path.split(os.sep)[-1]
        images =[]

        img = Image.open("tmp"+os.sep+"extract_image"+os.sep+filename)
        width = img.width
        with open(segments_path+os.sep+filename+"_segment.json", "r", encoding="UTF-8", errors='ignore') as segment_file:
            segments = ujson.load(segment_file)

        # Prepare the cropped images for the manual alignments
        crop_count = 0
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
                continue
            cropped_name ="manual_align"+os.sep+filename+os.sep+filename+"_"+str(crop_count)+".jpg" 
            images.append(cropped_name)
            cropped.save(cropped_name)
            crop_count += 1
        img.close()

        text_ref = retrieve_transcription(filename)

        generate_manual_align_webpage(filename, images, text_ref , usable )

if __name__ == '__main__':
    print("ok")

    generate_manual_alignments(2)
