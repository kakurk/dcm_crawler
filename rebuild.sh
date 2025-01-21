#!/bin/bash
# rebuild the container

if [ "$(whoami)" != "xnat" ]; then
  echo "Please change to user XNAT to run"
  exit
fi

docker build --tag dcm_crawler .