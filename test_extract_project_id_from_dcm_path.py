from dcm_crawler_xnat import extract_project_id_from_dcm_path

# where the data are archived on this machine
example_dcm_path = '/data/xnat/archive/burcs/arc001/test001_MR_1/SCANS/2/DICOM/01.118975065480874283224087851341860036220-2-100-dvd9sb.dcm'

# extract projectid
projectid = extract_project_id_from_dcm_path(example_dcm_path)

# print
print(projectid)