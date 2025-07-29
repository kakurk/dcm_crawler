# crawl through the dicom archives inspecting each dcm image to see if it
# contains the incorrect coil elements
#
# This script reads your XNAT authentication credentials (i.e., username, password) 
# from a hidden text file contained within the user's home directory.

# dependencies
from pydicom import dcmread
import os
import pandas as pd
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

import subprocess

def find_dicom_files(target_directory):
    try:
        result = subprocess.run(
            ['find', target_directory, '-path', '/data/xnat/archive/qa', '-prune', '-o', '-type', 'f', '-iname', '*.dcm', '-print'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        dicom_files = result.stdout.strip().split('\n') if result.stdout else []
        return dicom_files
    except subprocess.CalledProcessError as e:
        print("Error during find command:", e.stderr)
        return []

def extract_project_id_from_dcm_path(dcm_path):
    """
    Extract the XNAT project ID from a full DICOM file path.
    
    Assumes the path contains 'archive/{project_id}/arc001'.
    
    Args:
        dcm_path (str): Full path to the .dcm file
    
    Returns:
        str or None: Project ID if found, else None
    """
    # Normalize the path to handle any redundant separators
    parts = os.path.normpath(dcm_path).split(os.sep)

    try:
        archive_idx = parts.index('archive')
        if parts[archive_idx + 2] == 'arc001':
            return parts[archive_idx + 1]  # The project ID
    except (ValueError, IndexError):
        pass

    return None

def extract_session_id_from_dcm_path(dcm_path):
    """
    Extract the XNAT session ID from a full DICOM file path.
    
    Assumes the path contains 'arc001/{session_id}/SCANS'.
    
    Args:
        dcm_path (str): Full path to the .dcm file
    
    Returns:
        str or None: Project ID if found, else None
    """
    # Normalize the path to handle any redundant separators
    parts = os.path.normpath(dcm_path).split(os.sep)

    try:
        archive_idx = parts.index('arc001')
        if parts[archive_idx + 2] == 'SCANS':
            return parts[archive_idx + 1]  # The session ID
    except (ValueError, IndexError):
        pass

    return None

def get_subject_id(project_id, experiment_id, cursor):
    """
    Retrieves the subject ID and label for a given project ID and experiment ID
    using a pre-established PostgreSQL cursor.

    Args:
        project_id (str): XNAT project ID
        experiment_id (str): XNAT experiment/session label
        cursor (psycopg2.cursor): Active database cursor

    Returns:
        dict: {'subject_id': ..., 'subject_label': ...} or None
    """
    query = """
    SELECT subj.label AS subject_label
    FROM xnat_experimentdata e
    JOIN xnat_subjectassessordata sa ON sa.id = e.id
    JOIN xnat_subjectdata subj ON subj.id = sa.subject_id
    WHERE e.project = %s AND e.label = %s;
    """
    try:
        cursor.execute(query, (project_id, experiment_id))
        result = cursor.fetchone()
        return result.get('subject_label')
    except Exception as e:
        print(f"Query error for {experiment_id}: {e}")
        return None

def flush_datastore():
    if datastore:
        df = pd.DataFrame(datastore)
        df.to_csv(outfile, mode='a', header=False, compression="gzip", index=False, sep="|")
        datastore.clear()

if __name__ == "__main__":

    # Establish connection and cursor ONCE
    with psycopg2.connect(dbname="xnat",user="xnat",password="ozymandias",host="localhost",port=5432) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:

            # where the data are archived on this machine
            xnat_archive_location = '/data/xnat/archive'

            # find all dicom files
            # uses a call to the linux "find" command
            dcm_files = find_dicom_files(xnat_archive_location)

            BATCH_SIZE = 10000
            outfile = os.path.expanduser("~/crawl_results.psv.gz")
            datastore = []
            subject_cache = {}

            print('Crawling dcm files...\n')
            print(len(dcm_files), 'files found.\n')

            i = 0

            for d in dcm_files:

                i = i+1

                projectid = extract_project_id_from_dcm_path(d)
                sessionid = extract_session_id_from_dcm_path(d)

                # implement a cache approach to limit calls to the database
  
                key = (projectid, sessionid)
                if key in subject_cache:
                    subjectid = subject_cache[key]
                else:
                    subjectid = get_subject_id(projectid, sessionid, cur)
                    subject_cache[key] = subjectid

                dcm_filename = os.path.basename(d)

                # read dicom header fields
                #   We are interested in the following fields:
                #     SeriesNumber, SeriesDescription, StudyDate, ('0051','100F'),
                #     ('5200','9230')
                #   The last two fields are not always present, so we check for them
                #   separately.
                tags = ['StudyDescription', 'SeriesNumber', 'SeriesDescription', 'StudyDate', ('0051','100F'), ('5200','9230'), '']
                dcm_header = dcmread(d, stop_before_pixels=True, specific_tags=tags)
                projectid_dcm = dcm_header.get('StudyDescription')
                series_num  = dcm_header.get('SeriesNumber')
                series_desc = dcm_header.get('SeriesDescription')
                session_date = dcm_header.get('StudyDate')
                session_date_obj = datetime.datetime.strptime(session_date, '%Y%m%d')
                session_date_str = session_date_obj.strftime('%m-%d-%Y')

                # perform the check
                #   Check that the header has field ('00051', '100F')
                checkOne = ('00051','100F') in dcm_header
                checkTwo = ('5200','9230') in dcm_header
                if checkOne:
                    ele = dcm_header.get(('0051','100F'))
                    data = [projectid, projectid_dcm, subjectid, sessionid, session_date_str, series_num, series_desc, dcm_filename, 0, '(0051,100F)', str(ele)]
                    datastore.append(data)
                elif checkTwo:
                    entry = dcm_header.get(('5200','9230'))
                    # scroll through the entries within this field. There appears to be one entry per volume?
                    c = -1
                    for e in entry:
                        c = c + 1
                        try:
                            fieldEntry = e.get(('0021','11FE'))[0].get(('0021','114F'))
                        except:
                            fieldEntry = e.get(('0021','10FE'))[0].get(('0021','104F'))
                        data = [projectid, projectid_dcm, subjectid, sessionid, session_date_str, series_num, series_desc, dcm_filename, c, '(5200,9230)', str(fieldEntry)]
                        datastore.append(data)
                else:
                    data = [projectid, projectid_dcm, subjectid, sessionid, session_date_str, series_num, series_desc, dcm_filename, 0, '', '']
                    datastore.append(data)
                
                if len(datastore) > BATCH_SIZE:
                    print(f'{i}/{len(dcm_files)}\n')
                    flush_datastore()

            # write the results to a long csv file
            flush_datastore()
