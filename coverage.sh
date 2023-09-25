#!/bin/bash

coverage run --omit 'venv/*' -m pytest && coverage report -m