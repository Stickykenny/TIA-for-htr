"""
This file will create an image juxtaposing multiple cropped images so that they can in one single image 
before each cropped image will have an additional image 'mdvocr.png' to help locate the text

Usage : generate_juxtaposed
"""


from PIL import Image
import os
from PIL import ImageStat, ImageDraw


def generate_juxtaposed():

    # Source of segmented/cropped images
    cropped_dir = "manual_align"

    os.makedirs("juxtaposed", exist_ok=True)

    # Helper image to help google Lens start OCR on this line
    helper_image = Image.open("ressources"+os.sep+"mdvocr.png")
    interline_space = 150

    progress_count = 0  # Number of juxtaposed image
    skip_count = 0  # Number of image skipped because they were already aligned
    walk_list = list(os.walk(cropped_dir))

    # For every set of cropped images
    for dir, subfolders, files in walk_list[1:]:

        # Skip the image if it was manually aligned (json present)
        json_filename = dir.split(os.sep)[-1].replace(".jpg", ".json")
        if os.path.exists(cropped_dir+os.sep+json_filename):
            skip_count += 1
            continue

        # Images are sorted in alphabetical order
        files = sorted(files)

        # Fetch images
        images = [Image.open(dir+os.sep+file)
                  for file in files if file.endswith((".jpg", ".png"))]

        # Skip when no images are found
        if not images:
            continue

        # Retrieve median color of the images
        medians = [ImageStat.Stat(img).median for img in images]
        median_color = medians[len(medians)//2]

        # Define new image shape that will juxtaposed every cropped image
        # It will take into account the size of the helper image at the start of a line
        # Run the the code on one example to see a clear example of the wanted result
        sizes = [img.size for img in images]

        # Get the width of the helper image after being resized
        max_width = max(sizes, key=lambda sizes: sizes[1])
        first_img_width_max = int(
            helper_image.size[0]*max_width/helper_image.size[1])

        # Width of the new juxtaposed image ( with the addition of the helper image's width )
        max_width = max([size[0] for size in sizes]) + first_img_width_max*1.1

        # Height of the new image
        sum_height = sum([int(size[1]+interline_space) for size in sizes])

        # Create a blank new Image
        juxtaposed_image = Image.new('RGB', (max_width, sum_height),  color=tuple(
            median_color))  # Set default color to the median color

        # Concatenate all images one under another
        y_offset = 0  # y position as in mathematical position
        for img in images:

            # Width adjusted for the helper image
            new_width = int(
                helper_image.size[0]*img.size[1]/helper_image.size[1])

            # Paste the helper image and the image cropped
            juxtaposed_image.paste(helper_image.resize(
                (new_width, img.size[1])), (0, y_offset))
            juxtaposed_image.paste(img, (new_width, y_offset))

            # Create a black rectangle to separate each cropped image
            img1 = ImageDraw.Draw(juxtaposed_image)
            img1.rectangle(
                [(0, y_offset-(interline_space//2)-10), (max_width, y_offset-(interline_space//2)+10)], fill="#000000")

            # Offset for the new image
            y_offset += int(img.size[1]+interline_space)

            img.close()

        progress_count += 1
        # Show progress in steps of 10 images juxtaposed
        if progress_count % 10 == 0:
            print("juxtaposed "+str(progress_count)+"/"+str(len(walk_list)))

    print("juxtaposed "+str(progress_count)+"/"+str(len(walk_list)))
    print("A total of "+str(skip_count) +
          " images were skipped, because they were already aligned")

    helper_image.close()


if __name__ == "__main__":
    generate_juxtaposed()
