import dcm_crawler_xnat

# where the data are archived on this machine
dcm_crawler_xnat.datastore = ['','']
dcm_crawler_xnat.outfile = '/tmp/test.psv.gz'

# extract projectid
dcm_crawler_xnat.flush_datastore()

# show results
print(dcm_crawler_xnat.datastore)
print(dcm_crawler_xnat.outfile)