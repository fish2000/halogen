# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import shutil
import config
import tempfile

from tempfile import mktemp
from config import SHARED_LIBRARY_SUFFIX, STATIC_LIBRARY_SUFFIX, DEFAULT_VERBOSITY
from errors import HalogenError, GeneratorLoaderError, GenerationError
from generate import preload, generate, default_emits
from filesystem import TemporaryName, Directory, TemporaryDirectory, rm_rf
from utils import u8str

__all__ = ('CONF',
           'CompilerError', 'LinkerError', 'ArchiverError',
           'Generator',
           'Generators',
           'main')

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
        self.intermediate = kwargs.pop('intermediate', None)
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
            if self.intermediate:
                if not os.path.isdir(self.intermediate):
                    raise CompilerError("Non-existent intermediate artifact directory: %s" % self.intermediate)
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
                                    suffix="%s%so" % (splitbase[1], os.extsep),
                                    dir=self.intermediate)
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
    
    def __init__(self, conf, destination, directory=None, intermediate=None,
                                                          suffix="cpp",
                                                          prefix="yodogg",
                                          do_shared=True, do_static=True,
                                          do_preload=True,
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
        self.do_preload = do_shared and do_preload
        self.destination = Directory(pth=destination)
        if not self.destination.exists:
            raise CompilerError("Non-existant generator destination: %s" % self.destination.name)
        self.intermediate = Directory(pth=intermediate or tempfile.gettempdir())
        if not self.intermediate.exists:
            self.intermediate.makedirs()
        self.library = os.path.join(self.destination.name, "%s%s" % (self.prefix, SHARED_LIBRARY_SUFFIX))
        self.archive = os.path.join(self.destination.name, "%s%s" % (self.prefix, STATIC_LIBRARY_SUFFIX))
        self.directory = Directory(pth=directory)
        if not self.directory.exists:
            raise CompilerError("Non-existant generator source directory: %s" % self.directory.name)
        self._compiled = False
        self._linked = False
        self._archived = False
        self._preloaded = False
        self.sources = []
        self.prelink = []
        self.link_result = tuple()
        self.archive_result = tuple()
        self.preload_result = None
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
    def preloaded(self):
        """ Have all dynamically-linked generators successfully been preloaded? """
        return self._preloaded
    
    @property
    def source_count(self):
        """ Number (int) of generator sources found """
        return len(self.sources)
    
    @property
    def prelink_count(self):
        """ Number (int) of compiled but as-of-yet unlinked generators """
        return len(self.prelink)
    
    @property
    def object_suffix(self):
        """ The object-file suffix corresponding to the file suffix for this instance.
            Like e.g. if you initialized your instance like
            
            >>> generators = halogen.compile.Generators(suffix="cc")
            
            … your `generators.object_suffix` value will be “cc.o” -- as in, all of the
            pre-linked object code compilation artifacts will be named “something.cc.o”
            or whatever.
        """
        return u8str("%s%so" % (self.suffix, os.extsep))
    
    def compile_all(self):
        """ Attempt to compile all of the generator source files we discovered while walking
            the directory with which we were initialized.
            
            Internally, we use a halogen.filesystem.TemporaryName and a halogen.compile.Generator
            instance, both within context-managed nested scopes, for atomic operations. The
            return value is boolean: True if all discovered source files were successfully compiled
            and False if not -- in many such cases, one of the many sub-operations can and will
            throw an exception (q.v. halogen.errors supra).
        """
        if self.source_count < 1:
            raise CompilerError("can't find any compilation inputs: %s" % self.directory.name)
        if self.VERBOSE:
            print("Compiling %s generator source files\n" % self.source_count)
        for source in self.sources:
            with TemporaryName(suffix=self.object_suffix) as tn:
                with Generator(self.conf,
                               source=source, destination=tn.name,
                               intermediate=getattr(self.intermediate, "name",
                                                str(self.intermediate)),
                               verbose=self.VERBOSE) as gen:
                    if gen.compiled:
                        self.prelink.append(tn.do_not_destroy())
        if self.source_count == self.prelink_count:
            self._compiled = True
        return self.compiled
    
    def link(self):
        """ If compilation has previously been successful, the `link()` method will attempt
            to link all of the compiled object code artifacts into a dynamic-link library file,
            per the host platform (e.g. a DLL file on Windows*, a dylib on Mac OS X, a shared
            object binary on Linux and Solaris, etc).
            
            The `link()` method considers the discovery of an existing dynamic-link library file
            to be an error condition -- it will not, at the time of writing, overwrite a file
            at its destination path.
            
            * - that is, if this code ever runs on Windows, which I think would take some
                kind of crazy miracle, and/or someone giving me a Windows machine and a ton
                of spare time… you never know but I dunno
        """
        if not self.compiled:
            raise LinkerError("can't link before compilation: %s" % self.directory.name)
        if self.prelink_count < 1:
            raise LinkerError("no files available for linker: %s" % self.directory.name)
        if os.path.exists(self.library):
            raise LinkerError("can't overwrite linker output: %s" % self.library)
        if self.VERBOSE:
            print("Linking %s generators as %s\n" % (self.prelink_count,
                                    os.path.basename(self.library)))
        self.link_result += config.LD(self.conf,
                                      self.library,
                                     *self.prelink, verbose=self.VERBOSE)
        if len(self.link_result) > 0: # apres-link
            if len(self.link_result[1]) > 0: # failure
                raise LinkerError(self.link_result[1])
            self._linked = os.path.isfile(self.library)
        return self.linked
    
    def arch(self):
        """ If compilation has previously been successful, the `arch()` method will attempt
            to link all of the compiled object code artifacts into a static-link library file,
            per the host platform (e.g. a “lib” file on Windows*, a “.a” archive file on Mac
            OS X, Linux and Solaris, etc).
            
            The `arch()` method considers the discovery of an existing static-link library file
            to be an error condition -- it will not, at the time of writing, overwrite a file
            at its destination path.
            
            * - that is, if this code ever runs on Windows, which I think would take some
                kind of crazy miracle, and/or someone giving me a Windows machine and a ton
                of spare time… you never know but I dunno
        """
        if not self.compiled:
            raise ArchiverError("can't archive before compilation: %s" % self.directory.name)
        if self.prelink_count < 1:
            raise ArchiverError("no files available for archiver: %s" % self.directory.name)
        if os.path.exists(self.archive):
            raise ArchiverError("can't overwrite archiver output: %s" % self.archive)
        if self.VERBOSE:
            print("Archiving %s generators as %s\n" % (self.prelink_count,
                                      os.path.basename(self.archive)))
        self.archive_result += config.AR(self.conf,
                                         self.archive,
                                        *self.prelink, verbose=self.VERBOSE)
        if len(self.archive_result) > 0: # apres-arch
            if len(self.archive_result[1]) > 0: # failure
                raise ArchiverError(self.archive_result[1])
            self._archived = os.path.isfile(self.archive)
        return self.archived
    
    def preload_all(self):
        """ If both compilation and dynamic-library linking have been successful -- that is to
            say, both the `compile_all()` and `link()` have been successfully called without error,
            the `preload_all()` method will attempt to dynamic-link-load the binary library file
            generated by the `link()` call into the current running process.
            
            This method returns an object representing the result of the library-load call made
            to the `ctypes` module method `ctypes.cdll.LoadLibrary(…)`. The value of the read-only
            property `generators.preloaded` will thereafter appear as `True` iff the call to
            `halogen.generate.preload(…)` was able to successfully load the library via ctypes.
            
            Exceptions of type `halogen.errors.GeneratorLoaderError` can raise if things go awry.
        """
        # preload() may also raise GeneratorLoaderError:
        if self.preloaded:
            return self.preload_result
        if self.compiled and self.linked:
            try:
                self.preload_result = preload(self.library, verbose=self.VERBOSE)
            except GeneratorLoaderError as preload_error:
                raise preload_error
            else:
                self._preloaded = True
                return self.preload_result
        raise GeneratorLoaderError("can't preload from an uncompiled/unlinked generator")
    
    def loaded_generators(self):
        """ Return a tuple containing the names of all successfully loaded and currently available
            generator modules.
            
            This `loaded_generators()` method calls `hal.api.registered_generators()`, which
            uses Cython’s C++ bridge to call `Halide::GeneratorRegistry::enumerate()` and convert
            the returned `std::vector<std::string>` into a Python set of Python strings. That is,
            if the instance of `halogen.compile.Generators` has previously successfully ran its
            compilation phase, its link-dynamic phase, and its preload phase -- if not, it’ll
            just toss back an empty set without making any calls into Halide whatsoever.
        """
        if self.preloaded:
            import hal.api
            return hal.api.registered_generators()
        return set()
    
    def run(self, target='host', emit=default_emits, substitutions=None):
        """ Use the halogen.compile.Generators.run(…) method to run generators.
            
            All generator code that this instance knows about must have been previously compiled,
            dynamically linked, and preloaded. Assuming that all of these generators were properly
            programmed, they will then be available to halogen via the Halide Generator API --
            specifically the Generator Registry (q.v. `loaded_generators()` method docstring, supra).
        """
        # Check self-status:
        if not self.compiled:
            raise GenerationError("Can’t run() before first compiling, dynamic-linking, and preloading")
        if not self.linked:
            raise GenerationError("Can’t run() before first dynamic-linking and preloading")
        if not self.preloaded:
            raise GenerationError("Can’t run() before first preloading")
        
        # Check args:
        if not target:
            raise GenerationError("Target required when calling Generators::run(…)")
        if not emit:
            raise GenerationError("Values required for “emit” when calling Generators::run(…)")
        if len(emit) < 1:
            raise GenerationError("Values required for “emit” when calling Generators::run(…)")
        if not substitutions:
            substitutions = {}
        
        # Run generators, storing output files in $TMP/yodogg
        artifacts = generate(*self.loaded_generators(), verbose=self.VERBOSE,
                                                        target=target,
                                                        emit=tuple(emit),
                                                        output_directory=self.destination,
                                                        substitutions=substitutions)
        
        # Re-dictify:
        generated = { artifact[2].name : dict(base_path=artifact[0],
                                              outputs=artifact[1],
                                              module=artifact[2]) for artifact in artifacts }
        
        # TELL ME ABOUT IT.
        if self.VERBOSE:
            print("run(): Accreted %s total generation artifacts" % len(generated))
            print("run(): Module names: %s" % ", ".join(u8str(key) for key in sorted(generated.keys())))
        
        # Return redictified artifacts:
        return generated
    
    def clear(self):
        """ Delete temporary compilation artifacts: """
        # if self.VERBOSE:
        #     print("Cleaning up %s intermediates" % len(list(self.intermediate.ls(
        #                                                     pth=getattr(self.intermediate, "name",
        #                                                           u8str(self.intermediate)),
        #                                                     suffix=self.object_suffix))))
        for of in self.prelink:
            rm_rf(of)
    
    def __enter__(self):
        # 1: COMPILE ALL THE THINGS
        self.compile_all()
        
        # 2: link dynamically
        if self.compiled and self.do_shared:
            self.link()
        
        # 3: link statically (née 'archive')
        if self.compiled and self.do_static:
            self.arch()
        
        # 4: preload dynamic-linked output:
        if self.linked and self.do_preload:
            self.preload_all()
        
        # 5: return self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()


def main():
    
    """ Run the inline tests for the halogen.compile module """
    
    import tempfile
    from pprint import pprint
    directory = Directory(pth="/Users/fish/Dropbox/halogen/tests/generators")
    destination = Directory(pth=os.path.join(tempfile.gettempdir(), "yodogg"))
    zip_destination = "/tmp/"
    
    with TemporaryDirectory(prefix='yo-dogg-', suffix='') as td:
        
        with Generators(CONF, destination=td.name,
                              directory=directory,
                              verbose=DEFAULT_VERBOSITY) as gens:
            
            library = os.path.join(td.name, "%s%s" % ('yodogg', SHARED_LIBRARY_SUFFIX))
            archive = os.path.join(td.name, "%s%s" % ('yodogg', STATIC_LIBRARY_SUFFIX))
            
            compiled = gens.compiled and "YES" or "no"
            linked = gens.linked and "YES" or "no"
            archived = gens.archived and "YES" or "no"
            preloaded = gens.preloaded and "YES" or "no"
            
            print("IS IT COMPILED? -- %s" % compiled)
            print("IS IT LINKED? -- %s" % linked)
            print("IS IT ARCHIVED? -- %s" % archived)
            print("IS IT PRELOADED? -- %s" % preloaded)
            print("")
            
            loaded_generators = gens.loaded_generators()
            
            if DEFAULT_VERBOSITY:
                print("... SUCCESSFULLY LOADED LIBRARIES FROM %s" % gens.library)
                print("... THERE ARE %s GENERATORS LOADED FROM THAT LIBRARY, DOGG" % len(loaded_generators))
            
            if os.path.isfile(library):
                print("LIBRARY: %s" % library)
            if os.path.isfile(archive):
                print("ARCHIVE: %s" % archive)
            
            # Run generators:
            generated = gens.run(emit=('static_library',
                                       'stmt_html',
                                       'h', 'o',
                                       'cpp',
                                       'python_extension'))
            
            print('')
            pprint(generated, indent=4)
            print('')
            
            # Copy the library and archive files to $TMP/yodogg:
            if destination.exists:
                if DEFAULT_VERBOSITY:
                    print("Removing %s..." % destination.name)
                rm_rf(destination.name)
            if DEFAULT_VERBOSITY:
                print("Copying from %s to %s..." % (td.name, destination.name))
            td.copy_all(destination)
            
            with TemporaryName(suffix="zip", parent=zip_destination) as tz:
                if DEFAULT_VERBOSITY:
                    print("Zip-archiving from %s to %s..." % (destination.name, tz.name))
                Directory(destination).zip_archive(str(tz.name))
    
    # ... scope exit for Generators `gens` and TemporaryDirectory `td`

if __name__ == '__main__':
    main()