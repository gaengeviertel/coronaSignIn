#!/bin/bash

if [ -z ${VIRTUAL_ENV+x} ]; then
    echo "tdd.sh must be run in the virtual env" >&2
else
    rm "$(dirname "${BASH_SOURCE[0]}" )/.testmondata"
    exec ptw --clear -- --testmon
fi
