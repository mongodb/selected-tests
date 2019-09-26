#!/usr/bin/env bash

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

gunicorn --bind 0.0.0.0:8080 --workers 3 selectedtests.app.wsgi
