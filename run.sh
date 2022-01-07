#!/bin/bash

# make flask find api application
export FLASK_APP=./src/apimod/index.py
# export LOG_PATH=./log

# run flask listening on all interfaces in pipenv
pipenv run python -m flask run --debugger -h 0.0.0.0
