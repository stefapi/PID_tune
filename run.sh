#!/usr/bin/env bash

pipenv install
pipenv update
pipenv run pip freeze > requirements.txt
pipenv run python ./start.py
