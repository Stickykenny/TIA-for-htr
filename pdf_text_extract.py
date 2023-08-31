"""
pdf_text_extract.py: Contains functions for the processing of pdf files
"""

import os
# fitz is installed with 'pip install pymupdf'
import fitz  # import PyMuPdf better than PyPDF due to spaces appearing in words
import logging
from monitoring import timeit
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
logger = logging.getLogger("TIA_logger")


def extract_pdf_text(path: str) -> str:
    """
    Extract text from a pdf file

    Parameters :
        path :
            Path of the pdf file

    Returns :
        Text extracted from the pdf
    """

    # Check pdf extension
    if path.split(".")[-1] != "pdf":
        raise ValueError("File introduced isn't a pdf")

    with open(path, 'rb') as f:
        pdf = fitz.open(f)
        text = ""
        for page in pdf:
            text += page.get_text()  # extract plain text
        return text


def cut_syllabification(corpus: str) -> str:
    """
    Cut syllabification in the inputted corpus.
    It makes use of Selenium and this webpage https://igm.univ-mlv.fr/~gambette/text-processing/coupeCesure/

    Parameters :
        corpus :
            The corpus to cur the syllabification

    Returns :
        The curated corpus
    """

    # Setup driver
    driver = webdriver.Chrome()  # Google Chrome
    driver.get("https://igm.univ-mlv.fr/~gambette/text-processing/coupeCesure/")

    # Locate and in put text in the element of ID:textarea
    # Why not use .send_keys() : too slow, also Ctrl+V require additionnal install for Ubunbu
    corpus = corpus.replace("\n", "\\n")
    driver.execute_script(
        ' document.getElementById("textarea").value = "'+corpus+'" ')

    # Retrieve the submit button using XPATH and click on it
    submit_button = driver.find_element(
        By.XPATH, "/html/body/div/form/input[2]")
    submit_button.click()
    # Find the result using XPATH
    result_text = driver.find_element(
        By.XPATH, "//html/body/div/div[@id='theText']").text

    driver.quit()
    return result_text


@ timeit
def retrieve_pdfs_text(path_pdfs_dir: str, regroup: bool = False, syllabification_cut: bool = False,
                       pages_separator: str = "\n"+">"*10, output_folder: str = "text_extracted") -> None:
    """
    Given a directory, extract from each pdf files their text data.

    Parameters :
        path_pdfs_dir :
            Path to the directory containing pdf files
        regroup :
            If True, all texts extracted will be outputed into a single text file
            (default : False)
        syllabification_cut :
            If True, this function will take an extra steps to remove syllabification using a webpage
            (Default : False). If set to True, regroup will be ignored
        pages_separator :
            Separator used when texts are regrouped
            (Default = "\n"+">"*10)
        output_folder :
            Directory where files are saved
            (Default = "text_extracted")

    Returns :
        None
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    pdf_files = []
    for (_, _, filenames) in os.walk(path_pdfs_dir):
        pdf_files.extend(filenames)
    if regroup or syllabification_cut:
        # Regroup all texts in one file for mass process

        # Concatenate all texts retrieved into a single file
        with open("regroup.txt", 'w', encoding='UTF-8', errors="ignore") as new_file:
            for file in pdf_files:
                if file.split(".")[-1] != "pdf":
                    continue

                new_file.write(extract_pdf_text(path_pdfs_dir+os.sep+file))
                new_file.write(pages_separator)  # Separation between each file

        # If not syllabification_cut, text will only be regrouped into a single file
        if not syllabification_cut:
            logger.info("Check "+os.getcwd()+os.sep+"regroup.txt")
            return

        # If syllabification_cut, cut syllabification, also post-process the text
        # It will be all lowercased
        with open("regroup.txt", "r", encoding='UTF-8', errors='ignore') as regroup_file:
            regrouped_text = regroup_file.read()

        regrouped_text_cleaned = cut_syllabification(regrouped_text)

        curated_texts = regrouped_text_cleaned.split(pages_separator)
        index = 0
        for file in pdf_files:
            if file.split(".")[-1] != "pdf":
                print("skip this "+file)
                continue
            new_filename = file[:-3]+"gt.txt"
            with open(output_folder+os.sep+new_filename, 'w+', encoding='UTF-8', errors="ignore") as new_file:

                # In the transcription unreadable characters that were meant to be here are indicated uding []
                # We remove them because the OCR wouldn't be able to see them either.
                cleaned_text = re.sub(
                    r'\[[^]]*\]', '', curated_texts[index]).lower()
                new_file.write(cleaned_text)
                index += 1

        os.remove("regroup.txt")
        logger.info("Check "+os.getcwd()+os.sep+output_folder+os.sep)

    else:
        # Create a txt for each pdf
        for file in pdf_files:
            if file.split(".")[-1] != "pdf":
                break
            new_filename = file[:-3]+"gt.txt"
            with open(output_folder+os.sep+new_filename, 'w', encoding='UTF-8', errors="ignore") as new_file:
                new_file.write(extract_pdf_text(path_pdfs_dir+os.sep+file))
        logger.info("Check "+os.getcwd()+os.sep+output_folder+os.sep)
