#!/bin/bash

# make flask find api application
export FLASK_APP=./apimod/index.py

# activate the pipenv
source $(pipenv --venv)/bin/activate

# run flask listening on all interfaces
flask run -h 0.0.0.0
