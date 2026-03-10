import os
import psycopg2
import pytest
from psycopg2.extras import RealDictCursor
from dcm_crawler_xnat import extract_coil_string, extract_project_id_from_dcm_path, extract_session_id_from_dcm_path, get_subject_id, find_dicom_files

def test_extract_coil_string():
    
    # example DICOM header lines containing the coil string
    list_of_strings = [
        "(0021, 114f) Private tag data                    LO: 'HC1-7;NC1'",
        "(0021, 114f) Private tag data                    LO: 'H10'",
        "(0021, 114f) Private tag data                    LO: 'HC1-7;NC1,2'"
    ]

    # apply to our three examples
    results = [extract_coil_string(s) for s in list_of_strings]

    # expected results
    assert results == ['HC1-7;NC1', 'H10', 'HC1-7;NC1,2']

def test_extract_project_id_from_dcm_path():

    # first DICOM of test subjects in burcs project
    example_dcm_path = '/data/xnat/archive/burcs/arc001/test001_MR_1/SCANS/2/DICOM/01.118975065480874283224087851341860036220-2-100-dvd9sb.dcm'
    
    projectid = extract_project_id_from_dcm_path(example_dcm_path)
    
    # should be burcs
    assert projectid == 'burcs'

def test_extract_session_id_from_dcm_path():
    
    # first DICOM of test subjects in burcs project
    example_dcm_path = '/data/xnat/archive/burcs/arc001/test001_MR_1/SCANS/2/DICOM/01.118975065480874283224087851341860036220-2-100-dvd9sb.dcm'
    
    sessionid = extract_session_id_from_dcm_path(example_dcm_path)
    
    # should be test001_MR_1
    assert sessionid == 'test001_MR_1'

def test_flush_datastore():
    import dcm_crawler_xnat
    
    # creating a mini datastore and tmp file for testing
    dcm_crawler_xnat.datastore = ['','']
    dcm_crawler_xnat.outfile = '/tmp/test.psv.gz'
    
    # flush
    dcm_crawler_xnat.flush_datastore()
    
    # cleanup
    if os.path.exists('/tmp/test.psv.gz'):
        os.remove('/tmp/test.psv.gz')
    
    # datastore should be empty list
    assert dcm_crawler_xnat.datastore == []

def test_get_subject_id():
    try:
        conn = psycopg2.connect(
            dbname="xnat",
            user="xnat",
            password="ozymandias",
            host="localhost",
            port="5432"
        )
    except Exception as e:
        pytest.fail("Could not connect to XNAT postgres database: " + str(e))

    cur = conn.cursor(cursor_factory=RealDictCursor)

    subjectid = get_subject_id('burcs', 'test001_MR_1', cur)
    
    conn.close()

    assert subjectid == 'test001'

def test_find_dicoms():

    # where xnat stores the DICOM files on this machine
    target_dir = '/data/xnat/archive'

    # find dicoms modified within the last 7 days. Simple test to see if this runs without error.
    find_dicom_files(target_dir, modified_within_days=7)