from pathlib import Path
from dcm_crawler_xnat import find_dicom_files
import pdb

# where the data are archived on this machine
xnat_archive_location = '/data/xnat/archive'

# find all dicom files
dcm_files = find_dicom_files(xnat_archive_location, modified_within_days=7)

print(len(dcm_files), 'files found.\n')