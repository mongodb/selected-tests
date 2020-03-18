#!/usr/bin/env bash

FILE_DIR=$(dirname "$0")

. "$FILE_DIR/lib/setup_ssh_keys.sh" "selected_tests"

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

poetry run task-mappings --log-format json update
exit 0 # Since this is meant to be run as a cronjob in kubernetes, always exit 0.
