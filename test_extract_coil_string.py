import re
from dcm_crawler_xnat import extract_coil_string

list_of_strings = [
    "(0021, 114f) Private tag data                    LO: 'HC1-7;NC1'",
    "(0021, 114f) Private tag data                    LO: 'H10'",
    "(0021, 114f) Private tag data                    LO: 'HC1-7;NC1,2'"
]

results = [extract_coil_string(s) for s in list_of_strings]

print(results)