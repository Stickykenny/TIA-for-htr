import os
import fitz # import PyMuPdf better than PyPDF due to spaces appearing in words


def extract_pdf_text(path : str) -> str:
    """
    :param a:
    :raise ValueError: 
    :return: 
    """
    if path.split(".")[-1] != "pdf" :
        raise ValueError("File introduced isn't a pdf")

    with open(path, 'rb') as f:
        pdf = fitz.open(f)
        text = ""
        for page in pdf :
            text += page.get_text() # extract plain text
        return text


def retrieve_pdfs_text(path_pdfs_dir : str, regroup : bool=True, output_file : str="tmp_regroup.txt",
                        pages_separator : str="\n"+">"*10+"\n", output_folder : str= "text_extracted") -> None : 

    pdf_files=[]
    for (_,_, filenames) in os.walk(path_pdfs_dir):
        pdf_files.extend(filenames)

    if regroup :
        # Regroup all texts in one file for mass process
        with open(output_file, 'w') as new_file:
            for file in pdf_files :
                if file.split(".")[-1] != "pdf" :
                    break
                new_file.write(extract_pdf_text(path_pdfs_dir+os.sep+file))
                new_file.write(pages_separator) # Separation between each file
        print("Check "+os.getcwd()+os.sep+output_file)

    else :
        # Create a txt for each pdf
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        for file in pdf_files :
            if file.split(".")[-1] != "pdf" :
                break
            new_filename = file[:-3]+"txt"
            with open(output_folder+os.sep+new_filename, 'w') as new_file:
                new_file.write(extract_pdf_text(path_pdfs_dir+os.sep+file))
        print("Check "+os.getcwd()+os.sep+output_folder+os.sep)

if __name__ == "__main__" :


    path_PDFs_dir = "pdfTest"#"MDV-site-Xavier-Lang"
    retrieve_pdfs_text(path_PDFs_dir,regroup=False)
    #retrieve_pdfs_text(path_PDFs_dir, regroup = False)
