#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
#       halogen.py
#
#       Run a Halide generator as part of a build system
#       (c) 2016 Alexander Bohn, All Rights Reserved
#
from __future__ import print_function

import os, sys, re
from os.path import basename, dirname
from docopt import docopt # type: ignore

__version__ = '0.1.0'

halogen_source = basename(__file__)
libimread_base = os.path.abspath(os.environ.get('LIBIMREAD_BASE',
                 dirname(dirname(dirname(__file__)))))
generator_base = os.path.relpath(os.environ.get('HALOGEN_BASE',
                 os.path.join(libimread_base, 'build', 'halogen')))
scratch_output = os.path.relpath(
                 os.path.join(libimread_base, 'build', 'scratch_GENERATOR'))
version_string = "%s %s" % (halogen_source, __version__)

__doc__ = """
%(version)s

Usage:
  %(source)s GENERATOR    [-e BINARY   | --executable=BINARY]
                          [-o OUTDIR   | --output=OUTDIR]
                          [-t TARGETS  | --targets=TARGETS]
                          [-V | --verbose]
  %(source)s -h | --help | -v | --version
  
Options:
  -e BINARY, --executable=BINARY    specify path to executable [default: %(generators)s/GENERATOR].
  -o OUTDIR, --output=OUTDIR        specify output directory [default: %(scratch)s].
  -t TARGETS, --targets=TARGETS     specify comma-separated list of targets [default: host].
  -V, --verbose                     print verbose output.
  -h, --help                        show this text.
  -v, --version                     print version.

""" % {
    'version'       : version_string,
    'source'        : halogen_source,
    'generators'    : generator_base,
    'scratch'       : scratch_output
}

def cli(argv=None):
    if not argv:
        argv = sys.argv
    
    arguments = docopt(__doc__, argv=argv[1:],
                                help=True,
                                version=version_string)
    
    print(argv)
    print(arguments)
    # sys.exit()
    
    verbose = bool(arguments.get('--verbose'))
    name = arguments.get('GENERATOR')
    executable = re.sub('GENERATOR', name, arguments.get('--executable'))
    output = re.sub('GENERATOR', name, arguments.get('--output'))
    targets = [target.strip() for target in arguments.get('--targets').split(',')]
    
    if not os.path.isabs(executable):
        executable = os.path.join(libimread_base, executable)
    if not os.path.isabs(output):
        output = os.path.join(libimread_base, output)
    # if not os.path.isdir(output):
    #     os.makedirs(output)
    
    print('')
    print("VERBOSE: %s" % verbose)
    print("NAME: %s" % name)
    print("EXECUTABLE: %s" % executable)
    print("IS FILE? %s" % os.path.isfile(executable))
    print("OUTPUT: %s" % output)
    print("IS DIR? %s" % os.path.isdir(output))
    
    print('')
    print("TARGETS (%s): %s" % (len(targets), ", ".join(targets)))

def test():
    import tempfile
    # cli(sys.argv)
    # cli(['halogen.py', '--help', '--verbose'])
    # cli(['halogen.py', '--version'])
    cli(['halogen.py', '--output=%s' % tempfile.gettempdir(), '--targets=host,dev,yodogg', 'resize'])
    cli(['halogen.py', 'resize', '--output', tempfile.gettempdir(), '--targets', 'host,dev,yodogg'])
    cli(['halogen.py', 'resize'])

if __name__ == '__main__':
    test()