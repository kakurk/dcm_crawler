from dcm_crawler_xnat import flush_datastore

# where the data are archived on this machine
datastore = ['','']
outfile = '/tmp/test.psv.gz'

# extract projectid
flush_datastore()

# show results
print(datastore)
print(outfile)