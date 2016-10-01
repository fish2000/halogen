# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import shutil
import config
from tempfile import mktemp
from filesystem import TemporaryName

CONF = config.ConfigUnion(config.SysConfig(),
                          config.BrewedHalideConfig())
VERBOSE = True

# A few bespoke errors ... because yes on the occasions I do indulge myself,
# my version of a real TREAT-YO-SELF bender is: exception subclasses. It is true.

class CompilerError(Exception):
    """ A boo-boo during compilation """
    pass

class LinkerError(Exception):
    """ A link-time owie freakout """
    pass


class Generator(object):
    
    """ Atomically compile a generator from C++ source, using a specific “Config”-ish
        instance (like, from the config module) and writing the output to a specific
        destination. An intermediate temporary file is used, for some reason.
        Use it as a context manager for atomic auto-cleanup, if you're into that. """
    
    def __init__(self, conf, destination, source):
        self._compiled = False
        self.conf = conf
        self.destination = destination
        self.source = os.path.realpath(source)
        self.result = tuple()
    
    def compile(self):
        if not self._compiled:
            if not os.path.isfile(self.source):
                raise IOError("can't find compilation input: %s" % self.source)
            if os.path.exists(self.destination):
                raise IOError("can't overwrite compilation output: %s" % self.destination)
            splitbase = os.path.splitext(os.path.basename(self.source))
            self.transient = mktemp(prefix=splitbase[0],
                                    suffix="%s.o" % splitbase[1])
            self.result += config.CXX(self.conf,
                                      self.transient,
                                      self.source, verbose=VERBOSE)
    
    @property
    def compiled(self):
        return self._compiled
    
    def clear(self):
        if os.path.exists(self.transient):
            os.unlink(self.transient)
    
    def __enter__(self):
        self.compile()
        if len(self.result) > 0:
            if len(self.result[1]) > 0:
                # failure
                raise CompilerError(self.result[1])
            shutil.copyfile(self.transient, self.destination)
            self._compiled = os.path.exists(self.destination)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()


class Generators(object):
    
    """ Atomically compile all C++ source files from a given directory tree as generators,
        using a config instance (q.v. Generator, above) and then link all of them as a dynamic
        shared-object library. As a context manager, all of the intermediate Generator instances
        created during compilation (because that is how it works dogg, like by using a Generator
        for each discovered source file, OK) use a TemporaryName as their output targets -- so
        it's like POOF, no fuss no muss, basically """
    
    def __init__(self, conf, destination, directory=None, suffix="cpp"):
        if not directory:
            directory = os.getcwd()
        if not suffix:
            suffix = "cpp"
        self._compiled = False
        self._linked = False
        self.conf = conf
        self.destination = destination
        self.directory = directory
        self.suffix = suffix
        self.sources = []
        self.prelink = []
        self.result = tuple()
        for path, dirs, files in os.walk(self.directory,
                                         followlinks=True):
            for df in files:
                if df.lower().endswith(self.suffix):
                    self.sources.append(
                        os.path.realpath(
                            os.path.join(path, df)))
    
    @property
    def compiled(self):
        return self._compiled
    
    @property
    def linked(self):
        return self._linked
    
    def compile_all(self):
        if len(self.sources) < 1:
            raise IOError("can't find any compilation inputs: %s" % self.directory)
        for source in self.sources:
            with TemporaryName(suffix="%s.o" % self.suffix) as tn:
                with Generator(self.conf,
                               destination=tn.name,
                               source=source) as gen:
                    if gen.compiled:
                        self.prelink.append(tn.do_not_destroy())
        if len(self.sources) == len(self.prelink):
            self._compiled = True
    
    def link(self):
        if not self.compiled:
            raise LinkerError("can't link before compilation: %s" % self.directory)
        if len(self.prelink) < 1:
            raise LinkerError("no files available for linker: %s" % self.directory)
        if os.path.exists(self.destination):
            raise LinkerError("can't overwrite linker output: %s" % self.destination)
        self.result += config.LD(self.conf,
                                 self.destination,
                                *self.prelink, verbose=VERBOSE)
    
    def clear(self):
        for of in self.prelink:
            os.unlink(of)
    
    def __enter__(self):
        self.compile_all()
        self.link()
        if len(self.result) > 0:
            if len(self.result[1]) > 0:
                # failure
                raise LinkerError(self.result[1])
            self._linked = os.path.exists(self.destination)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()


if __name__ == '__main__':
    
    directory = "/Users/fish/Dropbox/halogen/generators"
    outshared = "/tmp/yodogg.dylib"
    
    if os.path.isfile(outshared):
        os.unlink(outshared)
    
    with Generators(CONF, outshared, directory) as gens:
        print("IS IT COMPILED? -- %s" % gens.compiled and "YES" or "no")
        print("IS IT LINKED? -- %s" % gens.compiled and "YES" or "no")

