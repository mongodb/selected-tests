#!/usr/bin/env bash

SSH_DIR=$HOME/.ssh
SRC_PATH=$(dirname "$0")

source "$SRC_PATH/lib/setup_ssh_keys.sh"
setup_ssh_keys "$SSH_DIR"

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

work-items process-test-mappings
exit 0 # Since this is meant to be run as a cronjob in kubernetes, always exit 0.
