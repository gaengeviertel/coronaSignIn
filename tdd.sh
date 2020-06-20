#!/bin/bash

if [ -z ${VIRTUAL_ENV+x} ]; then
    echo "tdd.sh must be run in the virtual env" >&2
else
    echo 'Executing `ptw --clear -- --testmon`'
    exec ptw --clear -- --testmon
fi
