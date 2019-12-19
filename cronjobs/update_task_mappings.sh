#!/usr/bin/env bash

SSH_DIR=$HOME/.ssh
FILE_DIR=$(dirname "$0")

source "$FILE_DIR/lib/setup_ssh_keys.sh"
setup_ssh_keys "$SSH_DIR"

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

task-mappings --log-format json update
exit 0 # Since this is meant to be run as a cronjob in kubernetes, always exit 0.
