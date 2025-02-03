#!/bin/bash
# open a shell inside the container

if [ "$(whoami)" != "xnat" ]; then
  echo "Please change to user XNAT to run"
  exit
fi

dcm_dir='/cnc/DATA/INVESTIGATORS/EXTERNALUSERS_MAUREENRITCHEY_BC'
tmp_dir='/tmp'

docker run -it -v $dcm_dir:/dcm_dir:ro -v $tmp_dir:/tmp_dir:rw -v /home/xnat:/out --entrypoint /bin/bash dcm_crawler