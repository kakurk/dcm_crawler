# crawl through the dicom archives inspecting each dcm image to see if it
# contains the incorrect coil elements
#
# This script reads your XNAT authentication credentials (i.e., username, password) 
# from a hidden text file contained within the user's home directory.

# dependencies
from pydicom import dcmread
import os
import pandas as pd
import pdb
import requests
import datetime
import xml.etree.ElementTree as ET

def find_dicom_files(target_directory):
    dicom_files = []
    for root, dirs, files in os.walk(target_directory):
        for file in files:
            if file.lower().endswith('.dcm'):
                full_path = os.path.abspath(os.path.join(root, file))
                dicom_files.append(full_path)
    return dicom_files

def create_jsession(xnat_url, username, password):
    """
    Authenticates with XNAT and retrieves a JSESSIONID for session-based access.

    Args:
        xnat_url (str): Base URL of the XNAT instance (e.g., https://central.xnat.org)
        username (str): XNAT username
        password (str): XNAT password

    Returns:
        str: JSESSIONID if authentication is successful, otherwise None
    """
    login_url = f"{xnat_url}/data/JSESSION"

    try:
        response = requests.post(login_url, auth=(username, password))
        if response.status_code == 200:
            jsession_id = response.cookies.get("JSESSIONID")
            if jsession_id:
                return jsession_id
            else:
                print("Login successful, but JSESSIONID not found in response.")
        else:
            print(f"Authentication failed. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error during authentication: {e}")
    
    return None

def close_xnat_session(xnat_url, jsession_id):
    """
    Closes (logs out) an XNAT session using a JSESSIONID.

    Args:
        xnat_url (str): Base URL of the XNAT instance (e.g., https://central.xnat.org)
        jsession_id (str): The JSESSIONID of the active session

    Returns:
        bool: True if the session was successfully closed, False otherwise
    """
    url = f"{xnat_url}/data/JSESSION"
    cookies = {"JSESSIONID": jsession_id}
    
    response = requests.delete(url, cookies=cookies)
    
    if response.status_code == 200:
        print("Session closed successfully.")
        return True
    else:
        print(f"Failed to close session. Status code: {response.status_code}")
        print("Response body:", response.text)
        return False

def get_subject_id_from_session(xnat_url, session_id, jsession_id, project=None):
    """
    Given an XNAT session ID, return the associated subject ID using JSESSIONID authentication.
    
    Args:
        xnat_url (str): Base URL of the XNAT instance (e.g., https://central.xnat.org)
        session_id (str): The experiment/session ID (e.g., XNAT_E00001)
        jsession_id (str): Value of the JSESSIONID cookie
        project (str, optional): Project ID if known (improves query precision)
    
    Returns:
        str: Subject ID associated with the session, or None if not found.
    """
    
    cookies = {
        "JSESSIONID": jsession_id
    }
    
    # Optional: use project path to disambiguate sessions across projects
    project_path = f"/projects/{project}" if project else ""
    url = f"{xnat_url}/data{project_path}/experiments/{session_id}?format=json"
    
    response = requests.get(url, cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('items')[0].get('data_fields').get('dcmPatientName')
    else:
        print(f"Failed to retrieve session. Status code: {response.status_code}")
        return None

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

def read_xnat_credentials(auth_file=".xnat_auth"):
    """
    Reads XNAT credentials from an XML-formatted file in the user's home directory.

    Expected XML format:
    <xnat>
      <xnat version="X.X">
        <url>https://xnat2.bu.edu</url>
        <username>username</username>
        <password>password</password>
      </xnat>
    </xnat>

    Args:
        auth_file (str): Name of the auth file (default is '.xnat_auth')

    Returns:
        tuple: (url, username, password), or raises RuntimeError if invalid
    """
    auth_path = os.path.expanduser(f"~/{auth_file}")

    if not os.path.exists(auth_path):
        raise RuntimeError(f"Auth file not found: {auth_path}")

    try:
        tree = ET.parse(auth_path)
        root = tree.getroot()

        # Find the first <xnat> child (the one with version attribute)
        xnat_node = root.find("xnat")

        if xnat_node is None:
            raise RuntimeError("Invalid format: Missing <xnat> element inside root.")

        url = xnat_node.findtext("url")
        username = xnat_node.findtext("username")
        password = xnat_node.findtext("password")

        if not all([url, username, password]):
            raise RuntimeError("Auth file must contain <url>, <username>, and <password>.")

        return url.strip(), username.strip(), password.strip()

    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse XML auth file: {e}")

if __name__ == "__main__":

    # where the data are archived on this machine
    xnat_archive_location = '/data/xnat/archive'

    # grab the users credentials for XNAT
    url, username, password = read_xnat_credentials()

    # log in to XNAT
    jsession = create_jsession(url, username, password)

    # find all dicom files
    dcm_files = find_dicom_files(xnat_archive_location)

    datastore = []

    print('Crawling dcm files...\n')

    i = 0

    for d in dcm_files:

        i = i+1

        print(f'{i}/{len(dcm_files)}\n')

        projectid = extract_project_id_from_dcm_path(d)
        sessionid = extract_session_id_from_dcm_path(d)
        subjectid = get_subject_id_from_session(url, sessionid, jsession, projectid)
        dcm_filename = os.path.basename(d)

        # read it into python
        dcm_header = dcmread(d)
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
            data = [projectid, subjectid, sessionid, session_date_str, series_num, series_desc, dcm_filename, 0, '(0051,100F)', str(ele)]
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
                data = [projectid, subjectid, sessionid, session_date_str, series_num, series_desc, dcm_filename, c, '(5200,9230)', str(fieldEntry)]
                datastore.append(data)
        else:
            print()
            print("Couldn't find either field.")
            print()
            data = [projectid, subjectid, sessionid, session_date_str, series_num, series_desc, dcm_filename, 0, '', '']
            datastore.append(data)

    # write the results to a long csv file
    dataFrame = pd.DataFrame(datastore, columns=['projectid', 'subjectid', 'sessionid', 'session_date', 'series_num', 'series_descr', 'dcm_filename', 'dcmArrayIdx', 'keyfield_hdr', 'keyfield_contents'])
    outfile = os.path.expanduser("~/crawl_results.psv.gz")
    dataFrame.to_csv(outfile, mode='a', header=False, compression="gzip", index=False, sep="|")

    # log out of XNAT
    close_xnat_session(url, jsession)