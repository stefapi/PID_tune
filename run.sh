#!/usr/bin/env bash
# this file is used to destroy a vagrant machine from the project and launch a fresh new one

pipenv install
pipenv update
pipenv run pip freeze > requirements.txt
pipenv run python ./start.py
