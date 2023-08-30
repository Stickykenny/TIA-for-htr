"""
Contains function to process ALTO XML files obtained from the ocr prediction
"""

import re


def remove_glyph(alto: str) -> str:
    """
    Remove Glyph tag in the ALTO file
    Glyph represent the character information

    Parameters :
        alto :
            String content of the alto file

    Returns :
        The text content without the glyph
    """

    # These are located inside the tag String :  <String .. > * </String>
    pattern = r'<String\s+[^>]*>(.*?)<\/String>'
    matches = re.findall(pattern, alto, re.DOTALL)
    for match in matches:
        alto = alto.replace(match, "")
    return alto


def reduce_to_line(alto: str) -> str:
    """
    Reduce multi-line of informations of word into a line for the whole sentence in the ALTO file

    Parameters :
        alto :
            String content of the alto file

    Returns :
        The text content reduced into lines inteads of word per word
    """

    # Concatenate informations words per words into a single tag for a single string
    for segment in alto.split("<TextLine")[1:]:
        lines = segment.split("\n")
        if len(lines) == 9:
            # A segment with only 1 word only has 9 lines of informations
            continue

        position_informations = lines[0]

        # Remove unnecessary attributes
        position_informations = re.sub(
            r'ID="[^\"]*"', "", position_informations)
        position_informations = re.sub(
            r'BASELINE="[^\"]*"', "", position_informations)
        position_informations = re.sub(
            r'TAGREFS="[^\"]*"', "", position_informations)

        # Skip the first 4 unrelated lines
        lines = lines[4:]

        # Replace the multi-lines of informations word per word into a single line
        content_pattern = re.escape('CONTENT="') + r'(.*?)' + re.escape('"')
        contents = " ".join(re.findall(content_pattern, "".join(lines)))
        alto = alto.replace("\n".join(
            lines), "    "*6+"<String CONTENT=\"" + contents+"\" "+position_informations+"</String>\n"+"    "*5+"</TextLine>\n\n")
    return alto
