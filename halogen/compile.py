# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import shutil
import config

from tempfile import mktemp
from config import SHARED_LIBRARY_SUFFIX, STATIC_LIBRARY_SUFFIX, DEFAULT_VERBOSITY
from errors import HalogenError, GeneratorLoaderError
from generate import preload, generate
from filesystem import TemporaryName, Directory, TemporaryDirectory, rm_rf

CONF = config.ConfigUnion(config.SysConfig(),
                          config.BrewedHalideConfig())

# What we need to load hal.api:
    
sys.path.append(os.path.dirname(
                os.path.dirname(__file__)))
sys.path.append(os.path.dirname(__file__))

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
    
    def __init__(self, conf, destination,
                             source,
                           **kwargs):
        self.VERBOSE = kwargs.pop('verbose', DEFAULT_VERBOSITY)
        self.conf = conf
        self.destination = destination
        self.source = os.path.realpath(source)
        self._compiled = False
        self.result = tuple()
        if self.VERBOSE:
            print("")
            print("Initializing generator: %s" % os.path.basename(self.source))
    
    def precompile(self):
        """ Validate the compilation source and destination file paths: """
        if self.VERBOSE:
            print("Pre-compiling: %s" % os.path.basename(self.source))
        if not self.compiled:
            if not os.path.isfile(self.source):
                raise CompilerError("can't find compilation input: %s" % self.source)
            if os.path.exists(self.destination):
                if os.path.isdir(self.destination):
                    raise CompilerError("can't replace a directory with compilation output: %s" % self.destination)
                raise CompilerError("can't overwrite with compilation output: %s" % self.destination)
        return True
    
    def compile(self):
        """ Execute the CXX compilation command, using our stored config instance,
            our validated source file, and a temporary output file name:
        """
        if self.VERBOSE:
            print("Compiling: %s" % os.path.basename(self.source))
            print("")
        if not self.compiled:
            splitbase = os.path.splitext(
                        os.path.basename(self.source))
            self.transient = mktemp(prefix=splitbase[0],
                                    suffix="%s.o" % splitbase[1])
            self.result += config.CXX(self.conf,
                                      self.transient,
                                      self.source, verbose=self.VERBOSE)
        return True
    
    def postcompile(self):
        """ Examine the results of the compilation command, ascertaining success
            or failure, raising exceptions as needed and copying the compilation
            output to the validated destination path if all is well:
        """
        if self.VERBOSE:
            print("Post-compiling: %s" % os.path.basename(self.source))
        if (not self.compiled) and (len(self.result) > 0): # apres-compilation
            if len(self.result[1]) > 0: # failure
                raise CompilerError(self.result[1])
            if not os.path.isfile(self.transient):
                raise CompilerError("compiler output isn’t a regular file: %s" % self.transient)
            shutil.copy2(self.transient, self.destination)
            self._compiled = os.path.isfile(self.destination)
        return self.compiled
    
    @property
    def compiled(self):
        """ Has the generator successfully been compiled? """
        return self._compiled
    
    def clear(self):
        """ Delete temporary compilation artifacts: """
        if self.VERBOSE:
            print("Cleaning up: %s" % os.path.basename(self.source))
        rm_rf(self.transient)
    
    def __enter__(self):
        self.precompile()
        self.compile()
        self.postcompile()
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
                                                          prefix="yodogg",
                                          do_shared=True, do_static=True,
                                        **kwargs):
        if not suffix:
            suffix = "cpp"
        if not prefix:
            prefix = "yodogg"
        self.VERBOSE = kwargs.pop('verbose', DEFAULT_VERBOSITY)
        self.conf = conf
        self.suffix = suffix
        self.prefix = prefix
        self.do_shared = do_shared
        self.do_static = do_static
        self.destination = destination
        self.library = os.path.join(destination, "%s%s" % (self.prefix, SHARED_LIBRARY_SUFFIX))
        self.archive = os.path.join(destination, "%s%s" % (self.prefix, STATIC_LIBRARY_SUFFIX))
        self.directory = Directory(pth=directory)
        self._compiled = False
        self._linked = False
        self._archived = False
        self.sources = []
        self.prelink = []
        self.link_result = tuple()
        self.archive_result = tuple()
        if self.VERBOSE:
            print(u"Scanning %s for “%s” files" % (self.directory.name, self.suffix))
        for path, dirs, files in self.directory.walk(followlinks=True):
            for df in files:
                if df.lower().endswith(self.suffix):
                    self.sources.append(os.path.realpath(
                                        os.path.join(path, df)))
        if self.VERBOSE:
            print("Found %s generator sources\n" % len(self.sources))
    
    @property
    def compiled(self):
        """ Have all generators successfully been compiled? """
        return self._compiled
    
    @property
    def linked(self):
        """ Have all generators successfully been dynamically linked? """
        return self._linked
    
    @property
    def archived(self):
        """ Have all generators successfully been statically linked (née archived)? """
        return self._archived
    
    @property
    def source_count(self):
        """ Number (int) of generator sources found """
        return len(self.sources)
    
    @property
    def prelink_count(self):
        """ Number (int) of compiled but as-of-yet unlinked generators """
        return len(self.prelink)
    
    def compile_all(self):
        if self.source_count < 1:
            raise CompilerError("can't find any compilation inputs: %s" % self.directory.name)
        for source in self.sources:
            with TemporaryName(suffix="%s.o" % self.suffix) as tn:
                with Generator(self.conf,
                               source=source, destination=tn.name,
                               verbose=self.VERBOSE) as gen:
                    if gen.compiled:
                        self.prelink.append(tn.do_not_destroy())
        if self.source_count == self.prelink_count:
            self._compiled = True
    
    def link(self):
        if not self.compiled:
            raise LinkerError("can't link before compilation: %s" % self.directory.name)
        if self.prelink_count < 1:
            raise LinkerError("no files available for linker: %s" % self.directory.name)
        if os.path.exists(self.library):
            raise LinkerError("can't overwrite linker output: %s" % self.library)
        self.link_result += config.LD(self.conf,
                                      self.library,
                                     *self.prelink, verbose=self.VERBOSE)
    
    def arch(self):
        if not self.compiled:
            raise ArchiverError("can't archive before compilation: %s" % self.directory.name)
        if self.prelink_count < 1:
            raise ArchiverError("no files available for archiver: %s" % self.directory.name)
        if os.path.exists(self.archive):
            raise ArchiverError("can't overwrite archiver output: %s" % self.archive)
        self.archive_result += config.AR(self.conf,
                                         self.archive,
                                        *self.prelink, verbose=self.VERBOSE)
    
    def preload_all(self):
        # preload() may also raise GeneratorLoaderError:
        if self.compiled and self.linked:
            return preload(self.library, verbose=self.VERBOSE)
        raise GeneratorLoaderError("can't preload from an uncompiled/unlinked generator")
    
    def loaded(self):
        import hal.api
        return hal.api.registered_generators()
    
    def clear(self):
        for of in self.prelink:
            rm_rf(of)
    
    def __enter__(self):
        # 1: COMPILE ALL THE THINGS
        self.compile_all()
        
        # 2: link dynamically
        if self.do_shared:
            if self.VERBOSE:
                print("Linking %s generators as %s\n" % (self.prelink_count,
                                        os.path.basename(self.library)))
            self.link()
            if len(self.link_result) > 0: # apres-link
                if len(self.link_result[1]) > 0: # failure
                    raise LinkerError(self.link_result[1])
                self._linked = os.path.isfile(self.library)
        
        # 3: link statically (née 'archive')
        if self.do_static:
            if self.VERBOSE:
                print("Archiving %s generators as %s\n" % (self.prelink_count,
                                          os.path.basename(self.archive)))
            self.arch()
            if len(self.archive_result) > 0: # apres-arch
                if len(self.archive_result[1]) > 0: # failure
                    raise ArchiverError(self.archive_result[1])
                self._archived = os.path.isfile(self.archive)
        
        # 4: return self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()


def main():
    
    import tempfile
    directory = "/Users/fish/Dropbox/halogen/tests/generators"
    destination = Directory(os.path.join(tempfile.gettempdir(), "yodogg"))
    zip_destination = "/tmp/"
    
    bsepths = None
    outputs = None
    modules = None
    
    with TemporaryDirectory(prefix='yo-dogg-', suffix='') as td:
        
        with Generators(CONF, destination=td.name,
                              directory=directory,
                              verbose=DEFAULT_VERBOSITY) as gens:
            
            library = os.path.join(td.name, "%s%s" % ('yodogg', SHARED_LIBRARY_SUFFIX))
            archive = os.path.join(td.name, "%s%s" % ('yodogg', STATIC_LIBRARY_SUFFIX))
            
            compiled = gens.compiled and "YES" or "no"
            linked = gens.linked and "YES" or "no"
            archived = gens.archived and "YES" or "no"
            
            print("IS IT COMPILED? -- %s" % compiled)
            print("IS IT LINKED? -- %s" % linked)
            print("IS IT ARCHIVED? -- %s" % archived)
            print("")
            
            try:
                preloaded = gens.preload_all()
            except GeneratorLoaderError as exc:
                if DEFAULT_VERBOSITY:
                    print("... FAILED TO LOAD LIBRARIES FROM %s" % gens.library)
                    print("%s" % str(exc))
                return
            else:
                if DEFAULT_VERBOSITY:
                    print("... RETURN VALUE OF gens.preload_all() is: %s" % str(preloaded))
            
            loaded_generators = gens.loaded()
            
            if DEFAULT_VERBOSITY:
                print("... SUCCESSFULLY LOADED LIBRARIES FROM %s" % gens.library)
                print("... THERE ARE %s GENERATORS LOADED FROM THAT LIBRARY, DOGG" % len(loaded_generators))
            
            if os.path.isfile(library):
                print("LIBRARY: %s" % library)
            if os.path.isfile(archive):
                print("ARCHIVE: %s" % archive)
            
            # Copy the library and archive files to $TMP/yodogg:
            if destination.exists:
                if DEFAULT_VERBOSITY:
                    print("Removing %s..." % destination.name)
                rm_rf(destination.name)
            if DEFAULT_VERBOSITY:
                print("Copying from %s to %s..." % (td.name, destination.name))
            td.copy_all(destination.name)
            
            with TemporaryName(suffix="zip", parent=zip_destination) as tz:
                if DEFAULT_VERBOSITY:
                    print("Zip-archiving from %s to %s..." % (destination.name, tz.name))
                Directory(destination).zip_archive(str(tz.name))
                # tz.do_not_destroy()
            
            if DEFAULT_VERBOSITY:
                print('')
            
            # Run generators, storing output files in $TMP/yodogg
            bsepths, outputs, modules = generate(*loaded_generators, verbose=DEFAULT_VERBOSITY,
                                                                     target='host',
                                                                     emit=('static_library',
                                                                           'stmt_html',
                                                                           'h', 'o', 'cpp',
                                                                           'python_extension'),
                                                                     output_directory=destination)
    
    # ... scope exit for Generators `gens` and TemporaryDirectory `td`

if __name__ == '__main__':
    main()