#!/bin/bash

coverage run  -m pytest && coverage report -m --omit 'test/*'