#!/usr/bin/env bash
rm -rf tray-server-env
python3 -m venv tray-server-env
source tray-server-env/bin/activate
unset PYTHONPATH
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
#echo "----- Created venv -------"
