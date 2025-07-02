from dcm_crawler_xnat import extract_session_id_from_dcm_path

# where the data are archived on this machine
example_dcm_path = '/data/xnat/archive'

# extract sessionid
sessionid = extract_session_id_from_dcm_path(example_dcm_path)

# print
print(sessionid)