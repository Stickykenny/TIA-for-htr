"""Usage : fix_dot_filename.py <path_to_pairs_directory>

Removes all additional dot in filename in indicated directory, because of ketos train implementation
"""

import os
import sys


def remove_additionnal_dots(txt: str):
    if txt.endswith((".jpg", ".png")):
        return ''.join(txt[:-4].split("."))+".jpg"
    if txt.endswith(".gt.txt"):
        return ''.join(txt[:-7].split("."))+".gt.txt"


if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) != 2:
        print(__doc__)
        exit()
    if not os.path.exists(sys.argv[1]):

        print(__doc__)
        print('Path does not exist')
        exit()

    directory = sys.argv[1]

    for dir, sub, files in os.walk(directory):
        for file in files:
            os.rename(dir+os.sep+file, dir+os.sep +
                      remove_additionnal_dots(file))

    print("done")
