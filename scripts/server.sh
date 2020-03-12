#!/usr/bin/env bash

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

poetry run uvicorn --host 0.0.0.0 --port 8080 --workers 1 selectedtests.app.asgi:app
