#!/bin/bash
# A test of the dcm_crawler script
# Assumes that the dcm_crawler has been wrapped up into a docker container called "dcm_crawler"

if [ "$(whoami)" != "xnat" ]; then
  echo "Please change to user XNAT to run"
  exit
fi

dcm_dir='/cnc/DATA/INVESTIGATORS/EXTERNALUSERS_MAUREENRITCHEY_BC'
tmp_dir='/tmp'

docker run --rm -v $dcm_dir:/dcm_dir:ro -v $tmp_dir:/tmp_dir:rw -v /home/xnat:/out dcm_crawler python dcm_crawler.py --dcm_dir /dcm_dir --tmp_dir /tmp_dir