# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import config

from compiledb import CDBJsonFile
from config import SHARED_LIBRARY_SUFFIX, STATIC_LIBRARY_SUFFIX, DEFAULT_VERBOSITY
from errors import HalogenError, GeneratorLoaderError, GenerationError
from generate import preload, generate, default_emits
from filesystem import rm_rf, temporary, TemporaryName
from filesystem import Directory, cd
from filesystem import TemporaryDirectory, Intermediate
from ocd import OCDList
from utils import u8str

__all__ = ('CONF', 'DEFAULT_MAXIMUM_GENERATOR_COUNT',
           'CompilerError', 'LinkerError', 'ArchiverError',
           'Generator',
           'Generators')

DEFAULT_MAXIMUM_GENERATOR_COUNT = 1024

CONF = config.ConfigUnion(config.SysConfig(),
                          config.BrewedHalideConfig())

# What we need to load halogen.api:

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
        if not conf:
            raise CompilerError("A config-ish instance is required")
        if not destination:
            raise CompilerError("A destination directory is required")
        if not source:
            raise CompilerError("A C++ generator source file is required")
        self.VERBOSE = bool(kwargs.pop('verbose', DEFAULT_VERBOSITY))
        self.cdb = kwargs.pop('cdb', None)
        self.conf = conf
        self.destination = os.fspath(destination)
        self.source = os.path.realpath(os.fspath(source))
        self.intermediate = 'intermediate' in kwargs and os.fspath(kwargs.pop('intermediate')) or None
        self._compiled = False
        self._destroy = True
        self.result = tuple()
        if self.VERBOSE:
            print("")
            print("Initialized C++ file compilation manager")
            print(f"*    Config class: {self.conf.name}")
            print(f"* Source filename: {os.path.basename(self.source)}")
            print(f"* Output filepath: {self.destination}")
            if self.cdb:
                print(f"*  Compilation DB: {repr(self.cdb)}")
            if self.intermediate:
                print(f"*    Intermediate: {self.intermediate}")
            print("")
    
    def precompile(self):
        """ Validate the compilation source and destination file paths: """
        if self.compiled:
            return True
        if self.VERBOSE:
            print(f"Pre-compiling: {os.path.basename(self.source)}")
        if self.intermediate:
            if not os.path.isdir(self.intermediate):
                raise CompilerError(f"Non-existent intermediate artifact directory: {self.intermediate}")
        if not os.path.isfile(self.source):
            raise CompilerError(f"can't find compilation input: {self.source}")
        if hasattr(self, 'transient'):
            if os.path.isfile(self.transient):
                rm_rf(self.transient)
        if os.path.exists(self.destination):
            if os.path.isdir(self.destination):
                raise CompilerError(f"can't replace a directory with compilation output: {self.destination}")
            raise CompilerError(f"can't overwrite with compilation output: {self.destination}")
        return True
    
    def compile(self):
        """ Execute the CXX compilation command, using our stored config instance,
            our validated source file, and a temporary output file name:
        """
        if self.compiled:
            return True
        sourcebase = os.path.basename(self.source)
        dirname = os.path.dirname(self.source)
        splitbase = os.path.splitext(sourcebase)
        suffix = os.path.splitext(self.destination)[1]
        self.transient = temporary(prefix=splitbase[0],
                                   suffix=suffix,
                                   parent=self.intermediate)
        if self.VERBOSE:
            print(f"Compiling: {sourcebase} to {os.path.basename(self.transient)}")
            print("")
        with cd(dirname) as cwd:
            # assert os.path.samefile(os.fspath(cwd), os.getcwd())
            self.result += config.CXX(self.conf, self.transient,
                                                 sourcebase,
                                                 cdb=self.cdb,
                                                 directory=cwd,
                                                 verbose=self.VERBOSE)
        return True
    
    def postcompile(self):
        """ Examine the results of the compilation command, ascertaining success
            or failure, raising exceptions as needed and copying the compilation
            output to the validated destination path if all is well:
        """
        import shutil
        if self.compiled:
            return True
        if self.VERBOSE:
            transbase = os.path.basename(self.transient)
            destbase = os.path.basename(self.destination)
            print(f"Post-compiling: {transbase} to {destbase}")
        if (not self.compiled) and (len(self.result) > 0): # apres-compilation
            if len(self.result[1]) > 0: # failure
                raise CompilerError(self.result[1])
            if not os.path.isfile(self.transient):
                raise CompilerError(f"compiler output isn’t a regular file: {self.transient}")
            shutil.copy2(self.transient, self.destination)
            self._compiled = os.path.isfile(self.destination)
        return self.compiled
    
    @property
    def compiled(self):
        """ Has the generator successfully been compiled? """
        return self._compiled
    
    @property
    def destroy(self):
        return self._destroy
    
    def do_not_destroy(self):
        """ Mark this Generator instance as one that should not automatically
            clean up its intermediate artifacts upon scope exit.
            
            This function returns the temporary file path, and may be called more
            than once without further side effects.
        """
        if self.compiled:
            self._destroy = False
            return self.transient
        return None
    
    def clear(self):
        """ Delete temporary compilation artifacts: """
        if self.destroy:
            if self.VERBOSE:
                print(f"Cleaning up: {os.path.basename(self.transient)}")
            return rm_rf(self.transient)
    
    def __enter__(self):
        self.precompile()
        self.compile()
        self.postcompile()
        return self
    
    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        # N.B. return False to throw, True to supress:
        self.clear()
        return exc_type is None


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
                                                          use_cdb=True,
                                          do_shared=True, do_static=True,
                                          do_preload=True,
                                        **kwargs):
        if not conf:
            raise CompilerError("A config-ish instance is required")
        if not suffix:
            suffix = "cpp"
        if not prefix:
            prefix = "yodogg"
        self.MAXIMUM =  int(kwargs.pop('maximum', DEFAULT_MAXIMUM_GENERATOR_COUNT))
        self.VERBOSE = bool(kwargs.pop('verbose', DEFAULT_VERBOSITY))
        self.conf = conf
        self.prefix = prefix
        self.suffix = suffix.lower()
        self.do_shared = do_shared
        self.do_static = do_static
        self.do_preload = do_shared and do_preload
        self.use_cdb = use_cdb
        self.destination = Directory(pth=destination)
        if not self.destination.exists:
            raise CompilerError(f"Non-existant generator destination: {self.destination}")
        self.library = self.destination.subpath(f"{self.prefix}{SHARED_LIBRARY_SUFFIX}")
        self.archive = self.destination.subpath(f"{self.prefix}{STATIC_LIBRARY_SUFFIX}")
        self.directory = Directory(pth=directory)
        if not self.directory.exists:
            raise CompilerError(f"Non-existant generator source directory: {self.directory}")
        self.intermediate = Intermediate(pth=intermediate)
        if not self.intermediate.exists:
            self.intermediate.makedirs()
        cdb = kwargs.pop('cdb', None)
        self.cdb = self.use_cdb and (cdb or CDBJsonFile(directory=self.intermediate)) or None
        self._precompiled = False
        self._compiled = False
        self._postcompiled = False
        self._linked = False
        self._archived = False
        self._preloaded = False
        self.sources = OCDList()
        self.prelink = OCDList()
        self.link_result = tuple()
        self.archive_result = tuple()
        self.preload_result = None
        if self.VERBOSE:
            print("")
            print("Initialized Halide generator compile/load/run suite:")
            print(f"* Config class: {self.conf.name}")
            print(f"* Using source: {self.directory}")
            print(f"* With targets: {self.destination}")
            if do_shared:
                print(f"*      Library: {self.library}")
            if do_static:
                print(f"*      Archive: {self.archive}")
            if use_cdb:
                print(f"*   Compile DB: {repr(self.cdb)}")
            print(f"* Intermediate: {self.intermediate}")
            print("")
    
    @property
    def precompiled(self):
        """ Have all generator sources been gathered? """
        return self._precompiled
    
    @property
    def compiled(self):
        """ Have all generators successfully been compiled? """
        return self._compiled
    
    @property
    def postcompiled(self):
        """ Has the compilation database (if any) been written? """
        return self._postcompiled
    
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
        return u8str(f"{self.suffix}{os.extsep}o")
    
    @property
    def compilation_database(self):
        if self.use_cdb:
            return self.cdb.name
        return None
    
    def precompile(self):
        """ Walk the path of the specified source directory, gathering all C++ generator
            source files that match the suffix furnished in the constructor, and storing
            the full filesystem paths of these files in the `self.sources` list of strings.
            
            This function returns a boolean indicating success or failure; gathering one or
            more source files is considered success, and finding no matches is a failure.
        """
        if self.precompiled:
            return True
        if self.VERBOSE:
            print(f"Scanning {self.directory} for “{self.suffix}” files")
        for path, dirs, files in self.directory.walk(followlinks=True):
            for df in files:
                if df.lower().endswith(self.suffix):
                    self.sources.append(os.path.realpath(
                                        os.path.join(path, df)))
        if self.source_count < self.MAXIMUM:
            if self.VERBOSE:
                print(f"Using {self.source_count} found generator sources")
                print("")
            self.MAXIMUM = self.source_count
        else:
            if self.VERBOSE:
                print(f"Using {self.MAXIMUM} of {self.source_count} generator sources found")
                print("")
            self.sources = OCDList(self.sources[:self.MAXIMUM])
        if self.source_count > 0:
            self._precompiled = True
        return self.precompiled
    
    def compile_all(self):
        """ Attempt to compile all of the generator source files we discovered while walking
            the directory with which we were initialized.
            
            Internally, we use a halogen.filesystem.TemporaryName and a halogen.compile.Generator
            instance, both within context-managed nested scopes, for atomic operations. The
            return value is boolean: True if all discovered source files were successfully compiled
            and False if not -- in many such cases, one of the many sub-operations can and will
            throw an exception (q.v. halogen.errors supra).
        """
        if self.compiled:
            return True
        if not self.precompiled:
            raise CompilerError(f"can't compile before precompilation: {self.directory}")
        if self.source_count < 1:
            raise CompilerError(f"can't find any compilation inputs: {self.directory}")
        if self.VERBOSE:
            print(f"Compiling {self.source_count} generator source files")
        for source in self.sources:
            # dirname = os.path.dirname(source)
            sourcebase = os.path.basename(source)
            splitbase = os.path.splitext(sourcebase)
            with TemporaryName(prefix=splitbase[0],
                               suffix=self.object_suffix) as tn:
                with Generator(self.conf, cdb=self.cdb,
                                          source=source,
                                          destination=os.fspath(tn),
                                          intermediate=os.fspath(self.intermediate),
                                          verbose=self.VERBOSE) as gen:
                    if gen.compiled:
                        gen.do_not_destroy()
                        self.prelink.append(tn.do_not_destroy())
        if self.VERBOSE:
            print("")
        if self.source_count == self.prelink_count:
            self._compiled = True
        return self.compiled
    
    def postcompile(self):
        """ If compilation has previously been successful, the `postcompile()` method will,
            if the `use_cdb` initializatiion option was True, attempt to write out a compilation
            database JSON file, using either the internal `self.cdb` compilation database
            instance, or, optionally, a compilation database of the users’ choosing, passed in
            at initialization as `cdb`.
            
            For more on the subject, q.v. http://clang.llvm.org/docs/JSONCompilationDatabase.html,
            the CompDB project at https://github.com/Sarcasm/compdb, or the source of the module
            `halogen.compiledb` supra.
        """
        if self.postcompiled:
            return True
        if not self.compiled:
            raise CompilerError(f"can't postcompile before compilation: {self.directory}")
        if self.prelink_count < 1:
            raise CompilerError(f"couldn't find any compilation outputs: {self.directory}")
        if self.VERBOSE:
            print(f"Writing {self.cdb.length} compilation database entries")
        self.cdb.write()
        if self.VERBOSE:
            print("")
        if self.compilation_database:
            if os.path.isfile(self.compilation_database):
                self._postcompiled = True
        return self.postcompiled
    
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
        if self.linked:
            return True
        if not self.compiled:
            raise LinkerError(f"can't link before compilation: {self.directory}")
        if self.prelink_count < 1:
            raise LinkerError(f"no files available for linker: {self.directory}")
        if os.path.exists(self.library):
            raise LinkerError(f"can't overwrite linker output: {self.library}")
        if self.VERBOSE:
            # print("")
            print(f"Linking {self.prelink_count} generators as {os.path.basename(self.library)}")
            print("")
        self.link_result += config.LD(self.conf,
                                      self.library,
                                     *self.prelink, verbose=self.VERBOSE)
        if len(self.link_result) > 0: # apres-link
            self._linked = os.path.isfile(self.library)
        if not self.linked:
            if len(self.link_result[1]) > 0: # failure
                raise LinkerError(self.link_result[1])
            raise LinkerError(f"Dynamic-link library file wasn’t created: {self.library}")
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
        if self.archived:
            return True
        if not self.compiled:
            raise ArchiverError(f"can't archive before compilation: {self.directory}")
        if self.prelink_count < 1:
            raise ArchiverError(f"no files available for archiver: {self.directory}")
        if os.path.exists(self.archive):
            raise ArchiverError(f"can't overwrite archiver output: {self.archive}")
        if self.VERBOSE:
            # print("")
            print(f"Archiving {self.prelink_count} generators as {os.path.basename(self.archive)}")
            print("")
        self.archive_result += config.AR(self.conf,
                                         self.archive,
                                        *self.prelink, verbose=self.VERBOSE)
        if len(self.archive_result) > 0: # apres-arch
            self._archived = os.path.isfile(self.archive)
        if not self.archived:
            if len(self.archive_result[1]) > 0: # failure
                raise ArchiverError(self.archive_result[1])
            raise ArchiverError(f"Static library archive file wasn’t created: {self.archive}")
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
            if self.VERBOSE:
                # print("")
                print(f"Preloading generators from {self.library}")
                # print("")
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
            
            This `loaded_generators()` method calls `halogen.api.registered_generators()`, which
            uses Cython’s C++ bridge to call `Halide::GeneratorRegistry::enumerate()` and convert
            the returned `std::vector<std::string>` into a Python set of Python strings. That is,
            if the instance of `halogen.compile.Generators` has previously successfully ran its
            compilation phase, its link-dynamic phase, and its preload phase -- if not, it’ll
            just toss back an empty set without making any calls into Halide whatsoever.
        """
        if self.preloaded:
            import api
            return api.registered_generators()
        return set()
    
    @property
    def loaded_count(self):
        """ Number (int) of dynamic-link-loaded generator modules currently available """
        return len(self.loaded_generators())
    
    def run(self, target='host', emit=default_emits, substitutions=None):
        """ Use the halogen.compile.Generators.run(…) method to run generators.
            
            All generator code that this instance knows about must have been previously compiled,
            dynamically linked, and preloaded. Assuming that all of these generators were properly
            programmed, they will then be available to halogen via the Halide Generator API --
            specifically the Generator Registry (q.v. `loaded_generators()` method docstring, supra).
        """
        # Check self-status:
        if not self.precompiled:
            raise GenerationError("Can’t run() before first precompiling, compiling, dynamic-linking, and preloading")
        if not self.compiled:
            raise GenerationError("Can’t run() before first compiling, dynamic-linking, and preloading")
        if not self.linked:
            raise GenerationError("Can’t run() before first dynamic-linking and preloading")
        if not self.preloaded:
            raise GenerationError("Can’t run() before first preloading")
        if self.loaded_count < 1:
            raise GenerationError("Can’t run() without one or more loaded generators")
        
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
            module_names = ", ".join(u8str(key) for key in sorted(generated.keys()))
            print(f"run(): Accreted {len(generated)} total generation artifacts")
            print(f"run(): Module names: {module_names}")
        
        # Return redictified artifacts:
        return generated
    
    def clear(self):
        """ Delete temporary compilation artifacts: """
        out = True
        for of in self.prelink:
            out &= rm_rf(of)
        return out
    
    def __enter__(self):
        # 0: start as you mean to go on:
        self.precompile()
        
        # 1: COMPILE ALL THE THINGS
        if self.precompiled:
            self.compile_all()
        
        # 2: Write out compilation database:
        if self.compiled and self.use_cdb:
            self.postcompile()
        
        # 3: link dynamically
        if self.compiled and self.do_shared:
            self.link()
        
        # 4: link statically (née 'archive')
        if self.compiled and self.do_static:
            self.arch()
        
        # 5: preload dynamic-linked output:
        if self.linked and self.do_preload:
            self.preload_all()
        
        # 6: return self
        return self
    
    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        # N.B. return False to throw, True to supress:
        self.intermediate.close()   # will destroy a TemporaryDirectory,
                                    # but not a plain Directory
        self.clear()                # will destroy all .o files
        return exc_type is None

def print_exception(exc):
    exc_name = str(type(exc).__name__)
    trace_output = f""" 
        • EXCEPTION:    {exc_name}
        • MESSAGE:     “{str(exc)}”
    """
    print(trace_output, file=sys.stderr)

def test(MAXIMUM_GENERATORS=2):
    
    """ Run the inline tests for the halogen.compile module """
    
    import tempfile
    from contextlib import ExitStack
    from pprint import pprint
    
    sys.path.append(os.path.dirname(
                    os.path.dirname(__file__)))
    
    import api
    
    directory = Directory(pth="/Users/fish/Dropbox/halogen/tests/generators")
    destination = Directory(pth=os.path.join(tempfile.gettempdir(), "yodogg"))
    zip_destination = os.path.realpath("/tmp")
    
    with TemporaryDirectory(prefix='yo-dogg-') as td:
        
        if not td.exists:
            print("X> TemporaryDirectory DOES NOT EXIST:")
            print(f"X> {td}")
        
        # We use a contextlib.ExitStack instance to separate out the construction
        # of the halogen.compile.Generators instance (q.v. immediately below) and
        # the call to __enter__ (q.v. right after that) so as to trap any and all
        # exceptions that may be thrown individually in either the constructor call
        # -- e.g. Generators.__init__ -- or Generators.__enter__ …
        
        stack = ExitStack()
        gens = Generators(CONF, directory=directory,
                                destination=td,
                                intermediate=td.subdirectory(".intermediate"),
                                maximum=MAXIMUM_GENERATORS,
                                verbose=DEFAULT_VERBOSITY,
                                use_cdb=True)
        
        # Preserve compilation artifacts:
        # td.do_not_destroy()
        
        try:
            # Calls Generators.__enter__(self=gens):
            stack.enter_context(gens)
        except CompilerError as exc:
            print_exception(exc)
            # gens.precompile() and gens.compile()
        except LinkerError as exc:
            print_exception(exc)
            # if gens.compiled and gens.do_static:
            #     gens.arch()
        except ArchiverError as exc:
            print_exception(exc)
            # if gens.compiled and gens.do_shared:
            #     gens.link()
            # if gens.linked and gens.do_preload:
            #     gens.preload_all()
        except GeneratorLoaderError as exc:
            print_exception(exc)
        except GenerationError as exc:
            print_exception(exc)
        else:
            with stack: # Exiting this scope calls Generators.__exit__(self=gens):
                
                precompiled = gens.precompiled and "YES" or "no"
                compiled = gens.compiled and "YES" or "no"
                postcompiled = gens.postcompiled and "YES" or "no"
                linked = gens.linked and "YES" or "no"
                archived = gens.archived and "YES" or "no"
                preloaded = gens.preloaded and "YES" or "no"
                
                print("")
                print(f"IS IT PRECOMPILED? -- {precompiled}")
                print(f"IS IT COMPILED? -- {compiled}")
                print(f"IS IT POSTCOMPILED? -- {postcompiled}")
                print(f"IS IT LINKED? -- {linked}")
                print(f"IS IT ARCHIVED? -- {archived}")
                print(f"IS IT PRELOADED? -- {preloaded}")
                print("")
                
                print(f"LIBRARY: {gens.library}")
                if gens.linked and os.path.exists(gens.library):
                    print("LIBRARY FILE EXISTS")
                
                print(f"ARCHIVE: {gens.archive}")
                if gens.archived and os.path.exists(gens.archive):
                    print("ARCHIVE FILE EXISTS")
                
                print(f"REGISTERED GENERATORS: {api.registered_generators()}")
                
                # loaded_generators = gens.loaded_generators()
                
                if DEFAULT_VERBOSITY:
                    if gens.loaded_count > 0:
                        print(f"... SUCCESSFULLY LOADED GENERATORS FROM LIBRARY {gens.library}")
                        print(f"... THERE ARE {gens.loaded_count} GENERATORS LOADED FROM THAT LIBRARY, DOGG")
                    else:
                        print(f"... NO GENERATORS COULD BE LOADED FROM LIBRARY {gens.library}")
                
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
                        print(f"Removing destination: {destination} …")
                    rm_rf(destination)
                
                if DEFAULT_VERBOSITY:
                    print(f"Copying from {td} to {destination} …")
                td.copy_all(destination)
                
                with TemporaryName(suffix="zip", parent=zip_destination) as tz:
                    if DEFAULT_VERBOSITY:
                        print(f"Zip-archiving destination contents to zipfile: {tz} …")
                    destination.zip_archive(tz)
                
                if gens.intermediate.exists:
                    if CDBJsonFile.in_directory(gens.intermediate):
                        if DEFAULT_VERBOSITY:
                            print("")
                            print(f"Found compilation DB file “{CDBJsonFile.filename}” in intermediate: {gens.intermediate}:")
                            with CDBJsonFile(directory=gens.intermediate) as cdb:
                                pprint(cdb.entries, indent=4)
                    if DEFAULT_VERBOSITY:
                        print("")
                        print(f"Listing files at intermediate: {gens.intermediate} …")
                    intermediate_list = OCDList(gens.intermediate.subpath(listentry) \
                                                for listentry in gens.intermediate.ls())
                    pprint(intermediate_list, indent=4)
                else:
                    print("X> Intermediate directory DOES NOT EXIST")
                    print(f"X> {gens.intermediate}")
                
                if destination.exists:
                    if DEFAULT_VERBOSITY:
                        print("")
                        print(f"Listing files at destination: {destination} …")
                    destination_list = OCDList(destination.subpath(listentry) \
                                               for listentry in destination.ls())
                    pprint(destination_list, indent=4)
                    if DEFAULT_VERBOSITY:
                        print(f"Removing destination: {destination} …")
                    rm_rf(destination)
                else:
                    print("X> Destination directory DOES NOT EXIST")
                    print(f"X> {destination}")
            
            # stack.pop()
    
    # ... scope exit for Generators `gens` and TemporaryDirectory `td`

if __name__ == '__main__':
    test()