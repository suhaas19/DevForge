#!/usr/bin/env bash
set -eu
cp -R "$(dirname "$0")/files/." .
if [ -f setup.sh ]; then bash setup.sh >/dev/null 2>&1 && rm -f setup.sh; fi
