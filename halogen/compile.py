# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import shutil
import config
from tempfile import mktemp
from errors import HalogenError, GeneratorError
from generate import preload
from filesystem import TemporaryName

CONF = config.ConfigUnion(config.SysConfig(),
                          config.BrewedHalideConfig())

DEFAULT_VERBOSITY = config.DEFAULT_VERBOSITY

# A few bespoke errors ... because yes on the occasions I do indulge myself,
# my version of a real TREAT-YO-SELF bender is: exception subclasses. It is true.
# All are subclasses of both IOError and halogen.errors.HalogenError:

class CompilerError(IOError, HalogenError):
    """ A boo-boo during compilation """
    pass

class LinkerError(IOError, HalogenError):
    """ A link-time owie freakout """
    pass

class ArchiverError(IOError, HalogenError):
    """ We couldn't be making the archive dood """
    pass


class Generator(object):
    
    """ Atomically compile a generator from C++ source, using a specific “Config”-ish
        instance (like, from the config module) and writing the output to a specific
        destination. An intermediate temporary file is used, for some reason.
        Use it as a context manager for atomic auto-cleanup, if you're into that. """
    
    def __init__(self, conf, destination, source, **kwargs):
        self.VERBOSE = kwargs.pop('verbose', DEFAULT_VERBOSITY)
        self._compiled = False
        self.conf = conf
        self.destination = destination
        self.source = os.path.realpath(source)
        self.result = tuple()
        if self.VERBOSE:
            print("Compiling generator: %s\n" % self.source)
    
    def compile(self):
        if not self._compiled:
            if not os.path.isfile(self.source):
                raise CompilerError("can't find compilation input: %s" % self.source)
            if os.path.exists(self.destination):
                raise CompilerError("can't overwrite compilation output: %s" % self.destination)
            splitbase = os.path.splitext(os.path.basename(self.source))
            self.transient = mktemp(prefix=splitbase[0],
                                    suffix="%s.o" % splitbase[1])
            self.result += config.CXX(self.conf,
                                      self.transient,
                                      self.source, verbose=self.VERBOSE)
    
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
            shutil.copy2(self.transient, self.destination)
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
    
    def __init__(self, conf, destination, directory=None, suffix="cpp",
                                          do_shared=True, do_static=True,
                                          **kwargs):
        if not directory:
            directory = os.getcwd()
        if not suffix:
            suffix = "cpp"
        self.VERBOSE = kwargs.pop('verbose', DEFAULT_VERBOSITY)
        self._compiled = False
        self._linked = False
        self._archived = False
        self.conf = conf
        self.destination = destination
        self.library = "%s%s" % (destination, config.SHARED_LIBRARY_SUFFIX)
        self.archive = "%s%s" % (destination, config.STATIC_LIBRARY_SUFFIX)
        self.directory = directory
        self.suffix = suffix
        self.do_shared = do_shared
        self.do_static = do_static
        self.sources = []
        self.prelink = []
        self.link_result = tuple()
        self.archive_result = tuple()
        if self.VERBOSE:
            print(u"Scanning %s for “%s” files" % (self.directory, self.suffix))
        for path, dirs, files in os.walk(self.directory,
                                         followlinks=True):
            for df in files:
                if df.lower().endswith(self.suffix):
                    self.sources.append(
                        os.path.realpath(
                            os.path.join(path, df)))
        if self.VERBOSE:
            print("Found %s generator sources\n" % len(self.sources))
    
    @property
    def compiled(self):
        return self._compiled
    
    @property
    def linked(self):
        return self._linked
    
    @property
    def archived(self):
        return self._archived
    
    def compile_all(self):
        if len(self.sources) < 1:
            raise CompilerError("can't find any compilation inputs: %s" % self.directory)
        for source in self.sources:
            with TemporaryName(suffix="%s.o" % self.suffix) as tn:
                with Generator(self.conf,
                               source=source, destination=tn.name,
                               verbose=self.VERBOSE) as gen:
                    if gen.compiled:
                        self.prelink.append(tn.do_not_destroy())
        if len(self.sources) == len(self.prelink):
            self._compiled = True
    
    def link(self):
        if not self.compiled:
            raise LinkerError("can't link before compilation: %s" % self.directory)
        if len(self.prelink) < 1:
            raise LinkerError("no files available for linker: %s" % self.directory)
        if os.path.exists(self.library):
            raise LinkerError("can't overwrite linker output: %s" % self.library)
        self.link_result += config.LD(self.conf,
                                      self.library,
                                     *self.prelink, verbose=self.VERBOSE)
    
    def arch(self):
        if not self.compiled:
            raise ArchiverError("can't archive before compilation: %s" % self.directory)
        if len(self.prelink) < 1:
            raise ArchiverError("no files available for archiver: %s" % self.directory)
        if os.path.exists(self.archive):
            raise ArchiverError("can't overwrite archiver output: %s" % self.archive)
        self.archive_result += config.AR(self.conf,
                                         self.archive,
                                        *self.prelink, verbose=self.VERBOSE)
    
    def preload_all(self):
        if self.compiled and self.linked:
            # preload() may also raise GeneratorError
            return preload(gens.library)
        else:
            raise GeneratorError("can't preload from an uncompiled/unlinked generator")
    
    def clear(self):
        for of in self.prelink:
            os.unlink(of)
    
    def __enter__(self):
        # 1: COMPILE ALL THE THINGS
        self.compile_all()
        
        # 2: link dynamically
        if self.do_shared:
            if self.VERBOSE:
                print("Linking %s generators as %s\n" % (len(self.prelink),
                                                         os.path.basename(self.library)))
            self.link()
            if len(self.link_result) > 0:
                if len(self.link_result[1]) > 0:
                    # failure
                    raise LinkerError(self.link_result[1])
                self._linked = os.path.exists(self.library)
        
        # 3: link statically (née 'archive')
        if self.do_static:
            if self.VERBOSE:
                print("Archiving %s generators as %s\n" % (len(self.prelink),
                                                           os.path.basename(self.archive)))
            self.arch()
            if len(self.archive_result) > 0:
                if len(self.archive_result[1]) > 0:
                    # failure
                    raise ArchiverError(self.archive_result[1])
                self._archived = os.path.exists(self.archive)
            return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()


if __name__ == '__main__':
    
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    sys.path.append(os.path.dirname(__file__))
    
    # sys.path addenda necessary to load hal.api:
    import hal.api
    
    directory = "/Users/fish/Dropbox/halogen/generators"
    destination = "/tmp/yodogg"
    
    library = "%s%s" % (destination, config.SHARED_LIBRARY_SUFFIX)
    archive = "%s%s" % (destination, config.STATIC_LIBRARY_SUFFIX)
    
    if os.path.isfile(library):
        os.unlink(library)
    if os.path.isfile(archive):
        os.unlink(archive)
    
    handle = None
    loaded_generators = 0
    
    with Generators(CONF, destination, directory, verbose=True) as gens:
        compiled = gens.compiled and "YES" or "no"
        linked = gens.linked and "YES" or "no"
        archived = gens.archived and "YES" or "no"
        
        print("IS IT COMPILED? -- %s" % compiled)
        print("IS IT LINKED? -- %s" % linked)
        print("IS IT ARCHIVED? -- %s" % archived)
        print("")
        
        try:
            hanlde = gens.preload_all()
        except GeneratorError, exc:
            if DEFAULT_VERBOSITY:
                print("... FAILED TO LOAD LIBRARIES FROM %s" % gens.library)
                print("%s" % str(exc))
        
        loaded_generators += len(hal.api.registered_generators())
        
        if DEFAULT_VERBOSITY:
            print("... SUCCESSFULLY LOADED LIBRARIES FROM %s" % gens.library)
            print("... THERE ARE %s GENERATORS LOADED FROM THAT LIBRARY, DOGG" % loaded_generators)
