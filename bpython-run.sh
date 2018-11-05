#!/usr/bin/env bash
: ${THISDIR:=$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)}
PYTHONPATH=${THISDIR}/halogen:${THISDIR} bpython -i ${THISDIR}/bpython-startup.py