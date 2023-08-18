# USAGE

`python3 add_align.py 10`
Using this command, 10 webpage will be created in which you will be able to manually align text/image.
It will produce JSON file that need to be move into this folder.
Then re-using the same command will process the alignment

The JSON file produced after the manual alignment need to be move into this folder. It is used for creating pairs of text/image and removing the unused cropped images, while also indicating the completition of the manual alignment. 

### Why doesn't the same command produce more webpage ?

    The script `add_align.py` do two tasks
        - 1/ Producing the webpage for manual alignments
        - 2/ Curate the data after manual alignment

By not making it deterministic, it generate additionnal webpage and folder (thus making harder to find the curated folder/cropped_images to pull out)

### How do I generate for webpage for manual alignments ?

`add_align.py` can take 1 or 2 arguments :
1. The first argument correspond to the number of webpage to create, by increasing it by 5, the script will produce 5 additionnal webpage, while still checking the 10 first.<br>
`python3 add align.py 15`
2. The second argument correspond to the number to skip, making it 5 results in the script skipping the 5 first, checking the 5 already created webpage and creating the 5 missing webpage<br>
`python3 add align.py 10 5`
