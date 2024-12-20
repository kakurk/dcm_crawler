# crawl through the dicom archives inspecting each dcm image to see if it 
# contains the incorrect coil elements

from pydicom import dcmread
import os
import argparse
import tarfile
import pandas as pd

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
dcm_files = get_files_with_extension(dcm_dir, '.tar.gz')

for dcm in dcm_files:

    print()
    print(dcm)
    print()

    datastore = []

    # unzip and untar the files
    this_tar_archive = tarfile.open(dcm)

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

            # perform the check
            #   Check that the header has field ('00051', '100F')
            checkOne = ('00051','100F') in dcm_header
            checkTwo = ('5200','9230') in dcm_header
            if checkOne:
                ele = dcm_header.get(('0051','100F'))
                print(ele)
                data = [this_tar_archive.name, fileparts[0], fileparts[1], 0, str(ele)]
                datastore.append(data)
            elif checkTwo:
                entry = dcm_header.get(('5200','9230'))
                # scroll through the entries within this field. There appears to be one entry per volume?
                c = -1
                for e in entry:
                    c = c + 1
                    fieldEntry = e.get(('0021','11FE'))[0].get(('0021','114F'))
                    print(fieldEntry)
                    data = [this_tar_archive.name, fileparts[0], fileparts[1], c, str(fieldEntry)]
                    datastore.append(data)
            else:
                print()
                print("Couldn't find either field.")
                print()
                data = [this_tar_archive.name, fileparts[0], fileparts[1], 0, '']
                datastore.append(data)

            # remove the extracted file
            os.remove(fullpath_to_dcm)

    # write the results to a long csv file
    dataFrame = pd.DataFrame(datastore, columns=['tarArchive','dirWithinArchive', 'filename', 'sequenceNum', 'keyfield'])
    dataFrame.to_csv('/out/log.csv', mode='a')




