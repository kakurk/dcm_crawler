from pathlib import Path
from dcm_crawler_xnat import find_dicom_files_with_find
import pdb

# where the data are archived on this machine
xnat_archive_location = '/data/xnat/archive'

# find all dicom files
dcm_files = find_dicom_files_with_find(xnat_archive_location)

pdb.set_trace()