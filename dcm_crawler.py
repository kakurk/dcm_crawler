# crawl through the dicom archives inspecting each dcm image to see if it
# contains the incorrect coil elements

# dependencies
from pydicom import dcmread
import os
import argparse
import tarfile
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta

def get_creation_time(filepath):
    """Gets the creation time of a file."""

    stat = os.stat(filepath)
    timestamp = stat.st_ctime  # Creation time in seconds since epoch
    creation_time = datetime.datetime.fromtimestamp(timestamp)
    return creation_time

def is_within_timeframe(target_date, start_date, end_date):
    """
    Checks if a target date is within a given timeframe.

    Args:
        target_date (datetime): The date to check.
        start_date (datetime): The start of the timeframe.
        end_date (datetime): The end of the timeframe.

    Returns:
        bool: True if the target date is within the timeframe, False otherwise.
    """

    return start_date <= target_date <= end_date

# helper function
def get_files_with_extension(directory, extension):
    files = []
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)) and filename.endswith(extension):
            fullpath_to_file = os.path.join(directory, filename)
            files.append(fullpath_to_file)
    return files

# Unpack the input arguments
parser = argparse.ArgumentParser(description="DCM Crawler")
parser.add_argument("--dcm_dir", default="./", help = "where the DICOMs are located", required=True)
parser.add_argument("--tmp_dir", default="./", help = "where can we temporarily extract dcm files to", required=True)
args, unknown_args = parser.parse_known_args()
dcm_dir = args.dcm_dir
tmp_dir = args.tmp_dir

# find all files in the dicom_dir. Filter for 1.) files 2.) that end in ".tar.gz"
tar_archives = get_files_with_extension(dcm_dir, '.tar.gz')

# get todays date
today          = datetime.date.today()
six_months_ago = today - relativedelta(months=6)

for this_archive in tar_archives:

    print()
    print(this_archive)
    print()

    datastore = []

    # when was this tar archive created?
    creation_time     = get_creation_time(this_archive)

    print('Creation Time:')
    print(creation_time)
    print()

    # is the creation time within the last 6 months?
    isWithinLastSixMonths = is_within_timeframe(target_date = creation_time.date(), start_date = six_months_ago, end_date = today)

    print('Is Within Last 6 Months:')
    print(isWithinLastSixMonths)
    print()

    if not isWithinLastSixMonths:
      continue

    # unzip and untar the files
    this_tar_archive = tarfile.open(this_archive)

    # scroll through the archive until we find a dcm file
    while True:

        # reads information from the first entry in the tar archive
        f = this_tar_archive.next()

        # if there are no more entries in the tar archive (i.e., we have scrolled through the entire thing) break the loop
        if f is None:
            print('Reached the files found in this archive')
            break

        # find the file extension for this file
        extension = os.path.splitext(f.name)[1]

        # if this file is a dcm file break the loop
        if extension in ['.dcm', '.dc3', '.dic', '.IMA']:

            print()
            print('dcm file found!')
            print()

            # extract this dcm file to a tmp directory
            this_tar_archive.extract(f, path = tmp_dir)
            fullpath_to_dcm = os.path.join(tmp_dir, f.name)
            fileparts = os.path.split(f.name)

            # read it into python
            dcm_header = dcmread(fullpath_to_dcm)
            series_num  = dcm_header.get('SeriesNumber')
            series_desc = dcm_header.get('SeriesDescription')

            # perform the check
            #   Check that the header has field ('00051', '100F')
            checkOne = ('00051','100F') in dcm_header
            checkTwo = ('5200','9230') in dcm_header
            if checkOne:
                ele = dcm_header.get(('0051','100F'))
                print(ele)
                data = [this_tar_archive.name, fileparts[0], fileparts[1], 0, series_num, series_desc, str(ele)]
                datastore.append(data)
            elif checkTwo:
                entry = dcm_header.get(('5200','9230'))
                # scroll through the entries within this field. There appears to be one entry per volume?
                c = -1
                for e in entry:
                    c = c + 1
                    # 
                    try:
                        fieldEntry = e.get(('0021','11FE'))[0].get(('0021','114F'))
                    except:
                        fieldEntry = e.get(('0021','10FE'))[0].get(('0021','104F'))
                    print(fieldEntry)
                    data = [this_tar_archive.name, fileparts[0], fileparts[1], c, series_num, series_desc, str(fieldEntry)]
                    datastore.append(data)
            else:
                print()
                print("Couldn't find either field.")
                print()
                data = [this_tar_archive.name, fileparts[0], fileparts[1], 0, series_num, series_desc, '']
                datastore.append(data)

            # remove the extracted file
            os.remove(fullpath_to_dcm)

    # write the results to a long csv file
    dataFrame = pd.DataFrame(datastore, columns=['tarArchive','dirWithinArchive', 'filename', 'sequenceNum', 'series_num', 'series_desc', 'keyfield'])
    dataFrame.to_csv('/out/log.csv', mode='a', header=False)