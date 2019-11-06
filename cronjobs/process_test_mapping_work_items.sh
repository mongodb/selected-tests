#!/bin/sh

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

work-items process-test-mappings
exit 0 # Since this is meant to be run as a cronjob in kubernetes, always exit 0.
