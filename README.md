# TIA-for-htr

Text-Image Alignment for Handwritten Text Recognition is a script tailored toward the MDV database to prepare pairs of text-image for training an HTR model using [kraken OCR](https://github.com/mittagessen/kraken)

> Kiessling, B. (2022). The Kraken OCR system (Version 4.1.2) [Computer software]. https://kraken.re

### Context

This project was realized in the context of an internship at LIGM for the 1st year of the Master's Degree in Computer Science 2022-2023 at Université Gustave Eiffel

# Installation

It is mentionned that kraken only runs on Linux or Mac OS X. Windows is not supported.

The script will require to install multiple python library, they can be installed using pip :

`pip install -r requirements.txt`

kraken will install version 1.2.2 of scikit-learn but it is not supported, due to this issue, scikit-learn need to be re-installed/downgraded with a specific version after

`pip install scikit-learn==1.1.2`

# Usage

```

`python3 main.py`
`python3 utils_extract path_images_cropped`
`ketos -vv train .... `

```

# How it works

### Data preparation

1. With a database of images and transcriptions of some of these images, the first step is to find these matches and extract them

2. ( In the case of the MDV database, the transcription were in pdf file with filename of dates, so additionnal processing was needed to fetch the right one and rename it)

3. Using kraken, the selected images are segmented and ocr-ed to obtain a rough result that will be aligned with the actual transcription

4. Using the ocr result, we create pairs of text-image for each segmented parts of the image associated with their correct transcription

5. Result produced tmp/cropped_image/\*/ will need to be regrouped into their parent folder using `python3 utils_extract.py tmp/cropped_image/`

### Saving Checkpoints

Some of these processes require some time, so to avoid wasting time, saves are created at completition for re-usability.

( Processes concerned are : the matching of usable image,the double page splitting, the segmentation, the ocr, the alignment and the cropping )

### How to train a model

To train/fine-tune a model using kraken/ketos it will be necessary to regroup all pairs of image_text into a single folder beforehand, and each cropped image must have his transcription in a filename of the same prefix (prefix meaning the string before the first "." ) and ending with '.gt.txt'

Then the training command can be launched ( see [ketos documentation](https://kraken.re/4.3.0/ketos.html) ) <br />
Example of command : `ketos -vv train -i base.mlmodel set4/*.jpg --resize new -p 0.75 -B 16 -f path`

### How do I reset ?

- For everything, delete the folder tmp/
- For the text retrieval, delete tmp/extract_pdf/ and extract_txt/
- For the pre-processing, delete tmp/extract_image and tmp/save/split_status.json
- For the segmentation, delete tmp/save/segment/ and tmp/save/ocr_save/
- For the OCR, delete tmp/save/ocr_save/
- For the alignments, delete /tmp/cropped_checklist.json and tmp/cropped_match/

# Project Structure

```
├── images/
│   └── >>> Contains images in their folder
├── models/
|   └── >>> Contains Kraken model
├── logs/
|   └── >>> Contains logs created each run
├── MDV-site-Xavier-Lang/
|   └── >>> Specified folder containing pdf
└── tmp/
    |── >>> Temporary files, can be deleted at the cost re-calculating everything
    ├── cropped_match/
    |   └── >>>  Contains for each image, pairs of image-text of their segmented parts
    ├── extract_image/
    |   └── >>> Contains images fetched
    ├── extract_pdf/
    |   └── >>> Contains PDFs fetched
    ├── extract_txt/
    |   └── >>> Contains text file extracted from PDFs in the tmp/extract_pdf/ directory
    ├── ocr_result/
    |   └── >>> Contains .pickle file to save data
    ├── save/
    |   └── >>>
    │   ├── match/
    |   |   └── >>> Contains dictionary of matches cotes-images as a pickle file, the filename is a hash of the result of os.walk(‘./images/)
    │   ├── ocr_save/
    |   |   └── >>> Contains ocr_record data obtained using kraken prediction
    │   └── segment/
    |   |   └── >>> Contains results of blla.segment()
    └── segmented/
        └── >>> Contains images segmented (baseline and boundaries shown)

```