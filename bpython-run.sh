#!/usr/bin/env bash
: ${THISDIR:=$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)}

# Courtesy the UNIX StackExchange:
# https://unix.stackexchange.com/a/124447/57742
function extendpath () {
    # usage:
    # $ extendpath /yo/dogg/bin
    # $ extendpath /yo/dogg/python-modules PYTHONPATH
    newpath="${1:?New path segment expected}"
    pathvar="${2:-PATH}"
    
    # check existence of new path:
    if [[ ! -d $newpath ]]; then
        echo "- Directory does not exist: ${newpath}"
        return 1
    fi
    
    # check named path variable (if any):
    if [[ ! ${!pathvar} ]]; then
        echo "- Path variable is unknown: “${pathvar}”"
        return 1
    fi
    
    # make a nameref pointing to the named variable --
    # q.v. `help declare` sub.
    typeset -n path="${pathvar}"
    case ":${!pathvar}:" in
        *:$newpath:*)  ;;
        *) path="$newpath:${!pathvar}"  ;;
    esac
    
    # re-export via nameref:
    export path
}

if [[ ! $PYTHONPATH ]]; then
    export PYTHONPATH="${THISDIR}"
fi

extendpath "${THISDIR}/halogen"  PYTHONPATH
extendpath "${HOME}/.script-bin" PYTHONPATH

# bpython -i ${THISDIR}/bpython-startup.py
python3 -m bpython --config=${HOME}/.config/bpython/config.py3 -i ${THISDIR}/bpython-startup.py