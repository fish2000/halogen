#!/usr/bin/env bash
pkg-config --debug --list-all |& grep -i "line>name:" | awk -F ":" '{print $2}' | sed 's/^[[:space:]]*//g'