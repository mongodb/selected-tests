#!/usr/bin/env bash

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

poetry run init-mongo create-indexes
