"""Usage : convert_lower.py <path_to_txt_directory>

Convert all txt files in indicated directory to lowercase
"""

import os
import sys


if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) != 2:
        print(__doc__)
        exit()
    if not os.path.exists(sys.argv[1]):

        print(__doc__)
        print('Path does not exist')
        exit()

    for dirpath, subfolders, files in os.walk(sys.argv[1]):
        for file in files:
            if file.endswith(".txt"):
                with open(dirpath+os.sep+file, "r", encoding="UTF-8", errors="ignore") as read_file:
                    text_content = read_file.read().lower()
                with open(dirpath+os.sep+file, "w", encoding="UTF-8", errors="ignore") as write_file:
                    write_file.write(text_content)
        print("Converted all txt files in "+dirpath+" to lowercase.")
