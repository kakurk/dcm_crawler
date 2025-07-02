from dcm_crawler_xnat import extract_project_id_from_dcm_path

# where the data are archived on this machine
example_dcm_path = '/data/xnat/archive'

# extract projectid
projectid = extract_project_id_from_dcm_path(example_dcm_path)

# print
print(projectid)