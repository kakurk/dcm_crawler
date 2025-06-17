#!/bin/bash
# Bash script for scanning the BU CNC archives
# first input argument is the path to a text file containing the full path to each archive you would like to scan

# update the user that we are scanning the archives
echo ""
echo Scanning Archives...
echo ""

# create a bash array "archives_to_scan" and read in the entries from that array from the text file input as the first input argument
declare -a archives_to_scan

while read -r line; do
   archives_to_scan+=("$line")
done < "$1"

# scan each archive using the dcm_crawler routine
# the routine will write out a log file
for element in "${archives_to_scan[@]}"
do
        echo ""
        echo "Archive:"
        echo "$element"
        echo ""
        python dcm_crawler.py --dcm_dir $element --tmp_dir /tmp
done