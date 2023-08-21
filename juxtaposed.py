"""
Minor script producing juxtaposition of multiple cropped images and their transcription
"""

from PIL import Image
import os
from PIL import ImageStat, ImageDraw

if __name__ == "__main__":

    cropped_dir = "manual_align"
    os.makedirs("juxtaposed", exist_ok=True)

    first_img = Image.open("ressources"+os.sep+"mdvocr.png")


    progress_count = 0
    walk_list =  list(os.walk(cropped_dir))

    for dir, subfolders, files in walk_list[1:]:

        files = sorted(files)
        # Fetch images
        images = [Image.open(dir+os.sep+file)
                  for file in files if file.endswith((".jpg", ".png"))]

        medians = [ImageStat.Stat(img).median for img in images]
        median_color = medians[len(medians)//2]
        # Skip when no images are found
        if not images:
            continue

        # Define new image shape
        sizes = [img.size for img in images]
        max_width = max([size[0] for size in sizes])+first_img.size[0]+500
        sum_height = sum([int(size[1]+150) for size in sizes])
        juxtaposed_image = Image.new('RGB', (max_width, sum_height),  color=tuple(median_color))  # Set default color to white

        # Concatenate all images one under another
        y_offset = 0
        for img in images:
            new_width = int(first_img.size[0]*img.size[1]/first_img.size[1])
            juxtaposed_image.paste(first_img.resize((new_width,img.size[1])), (0, y_offset))
            juxtaposed_image.paste(img, (new_width, y_offset))

            black_separator = Image.new("RGB", (max_width, 150))
            
            ## create  rectangleimage
            #
            img1 = ImageDraw.Draw(juxtaposed_image)  
            img1.rectangle([  (0,y_offset-85),(max_width,y_offset-65) ], fill ="#000000")

            y_offset += int(img.size[1]+150)
            img.close()

        # Save the juxtaposed img into juxtaposed/
        img_filename = dir.split(os.sep)[-1][:-4]
        juxtaposed_image.save("juxtaposed"+os.sep +
                              img_filename+"_juxtaposed.jpg")
        juxtaposed_image.close()

        # Retrieve the transcriptions and append it to a list
        transcriptions = [dir+os.sep +
                          file for file in files if file.endswith((".txt"))]
        transcripts_list = []
        for transcript in transcriptions:
            with open(transcript, "r", encoding="UTF-8", errors="ignore") as text_file:
                transcripts_list.append(text_file.read().replace("\n", ""))

        progress_count+=1
        print("juxtaposed "+str(progress_count)+"/"+str(len(walk_list)))

    first_img.close()