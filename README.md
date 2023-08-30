# TIA-for-htr

Text-Image Alignment for Handwritten Text Recognition is a script tailored toward the MDV database to prepare pairs of text/image for training an HTR model using [Kraken OCR](https://github.com/mittagessen/kraken)

> Kiessling, B. (2022). The Kraken OCR system (Version 4.1.2) [Computer software]. https://kraken.re

### Context

This project was realized in the context of an internship at LIGM for the 1st year of the Master's Degree in Computer Science 2022-2023 at Université Gustave Eiffel

# Installation

It is mentionned that Kraken only runs on **Linux or Mac OS X**. Windows is not supported.

The script will require to install multiple python library, they can be installed using pip :

`pip install -r requirements.txt`

Kraken will install version 1.2.2 of scikit-learn but it is not supported, due to this issue, scikit-learn need to be re-installed/downgraded with a specific version after

`pip install scikit-learn==1.1.2`

For the version using google Lens, install Tkinter <br>
`sudo apt install python3-tk (Unix)` or `pip install tk (Windows)`

# Usage

#### Input

For the general cases of dataset : <br>
Put all images into `tmp/extract_image` and their transcriptions into `tmp/extract_txt`<br>
(Like the name suggest files in `tmp/` may be altered)

For the MDV dataset : <br>
Put all images into the `images/` directory and all pdfs `MDV-site-Xavier-Lang/` or directly their txt files in `tmp/extract_txt`

#### Command

```

`python3 main.py`
`python3 add_align.py [number_to_align]`
`ketos -vv train .... `

```

_For this project, image files were named like "Ms1467-36-3 2.jpg" and their id/cote are in this format "1467-36-3" .
Given the situation, it is likely that the Data Preparation part in main.py can be commented_

# How it works

### Data preparation

1. With a database of images and transcriptions of some of these images, the first step is to find these matches and extract them

2. ( In the case of the MDV database, the transcription were in pdf file with filename of dates, so additionnal processing was needed to fetch the right one and rename it)

### Alignment

3. Using Kraken, the selected images are segmented and ocr-ed to obtain a rough result that will be aligned with the actual transcription

4. Using the ocr result, we create pairs of text/image for each segmented parts of the image associated with their correct transcription

5. Result produced tmp/cropped_image/\*/ will need to be regrouped into their parent folder using `python3 utils_extract.py tmp/cropped_image/`

### Saving Checkpoints

Some of these processes require some time, so to avoid wasting time, saves are created at completition for re-usability.

( Processes concerned are : the matching of usable image,the double page splitting, the segmentation, the ocr, the alignment and the cropping )

### Manual alignments

see [Usage of add_align.py](/manual_align/README.md)

The main script is made for automatic text/image alignment, a flaw that comes is the result vary considerably on the default model used.
In the case of this project, the recognition produced were mostly okay-ish with the chosen model and improved with the alignments. But none of the harder image could be aligned making the dataset produced highly biased towards already passable image. <br />
A solution available is to manually align these images. <br />

Using add_align.py, web page will be generated with the ability to manually align. The web page will then produce a json that has to be moved into the mmanual_align folder. Re-using add_align.py will then clean the unused cropped image.

### How to train a model

To train/fine-tune a model using Kraken/ketos it will be necessary to regroup all pairs of text/image into a single folder beforehand, and each cropped image must have his transcription in a filename of the same prefix (prefix meaning the string before the first "." ) and ending with '.gt.txt'

Then the training command can be launched ( see [ketos documentation](https://kraken.re/4.3.0/ketos.html) ) <br />
Example of command : `ketos -vv train -i base.mlmodel pairs/*/*.jpg --resize new -p 0.75 -B 16 -f path`

### How do I reset ?

- For everything, delete the folder `tmp/` and `manual_align/`
- For the text retrieval, delete `tmp/extract_pdf/` and `extract_txt/`
- For the pre-processing, delete `tmp/extract_image` and `tmp/save/split_status.json`
- For the segmentation, delete `tmp/save/segment/` and `tmp/save/ocr_save/`
- For the OCR, delete `tmp/save/ocr_save/`
- For the alignments, delete `tmp/cropped_match/`
- For the manual alignments, delete `jsons in the manual_align/` folder

# Project Structure

```
├── images/
│   └── >>> Contains unfiltered images in their folder
|           If the data is already associated with a transcription (same prefix) ignore this folder
├── models/
|   └── >>> Contains Kraken model
├── logs/
|   └── >>> Contains logs created each run
├── ressources/
|   └── >>> Contains various files used by the program
├── manual_align/
|   └── >>> Contains files for manually align text/image
├── MDV-site-Xavier-Lang/
|   └── >>> Specified folder containing pdf
└── tmp/
    |── >>> Temporary files, can be deleted at the cost re-calculating everything
    ├── cropped_match/
    |   └── >>>  Contains for each image, pairs of text/image of their segmented parts
    ├── extract_image/
    |   └── >>> Contains images fetched to process
    ├── extract_pdf/
    |   └── >>> Contains PDFs fetched
    ├── extract_txt/
    |   └── >>> Contains text transcriptions
    |           These files are the reference to which we align the OCR prediction
    ├── ocr_result/
    |   └── >>> Contains .pickle file to save data
    ├── save/
    |   ├── >>>
    │   ├── match/
    |   |   └── >>> Contains dictionary of matches cotes-images as a pickle file, the filename is a hash of the result of os.walk(‘./images/)
    │   ├── ocr_save/
    |   |   └── >>> Contains ocr_record data obtained using Kraken prediction
    │   ├── segment/
    |   |   └── >>> Contains results of blla.segment() (= segmentation data)
    |   └── segment_stats/
    |       └── >>> Contains statistics of the alignments produced, an histogram and a json.
    |           (see monitoring.quantify_segment_used() for the json structure.)
    └── segmented/
        └── >>> Contains images segmented (boundaries shown)

```
