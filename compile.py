# -*- coding: utf-8 -*-

from __future__ import print_function

from tempfile import mktemp
import os
import shutil
import config

# What we are going for is:

# TO COMPILE GENERATOR SOURCE (AS BEFORE, BUT SANS `GenGen.cpp`):
#
# clang -fno-strict-aliasing -fno-common -dynamic -g -O2 -DNDEBUG -g -fwrapv -O3 -Wall -Wstrict-prototypes
# -I/usr/local/include -I/usr/local/opt/openssl/include -I/usr/local/opt/sqlite/include
# -I/usr/local/Cellar/python/2.7.12/Frameworks/Python.framework/Versions/2.7/include/python2.7
# -c ./generators/lesson_16_rgb_generate.cpp -o build/temp.macosx-10.11-x86_64-2.7/./generators/lesson_16_rgb_generate.o 
# -Wno-unused-function -Wno-unneeded-internal-declaration
# -O3 -fno-rtti -funroll-loops -mtune=native -std=c++1z -stdlib=libc++
#
# ... note that this generally sucks (-O2 and then two -O3 flags?!) but should probably
#     favor suckitude-preservation over suck-optimization; likely it will be derived from
#     whatever `python-config --cflags` barfs up. Halide include directory should either
#     be explicitly specified (to, like, the function or whatever that does this) or
#     maybe use `brew --prefix halide` if possible -- or maybe not, I don't fucking know,
#     why don't you just tell me MIISSSSSSTER SYSADMIN

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


class TemporaryName(object):
    
    """ This is like NamedTemporaryFile without any of the actual stuff;
        it just makes a file name -- YOU have to make shit happen with it.
        But: should you cause such scatalogical events to transpire, this
        class (when invoked as a context manager) will clean it up for you.
        Unless you say not to. Really it's your call dogg I could give AF """
    
    def __init__(self, prefix="yo-dogg-", suffix="tmp"):
        self._name = mktemp(prefix=prefix, suffix=".%s" % suffix)
        self._destroy = True
        self.prefix = prefix
        self.suffix = suffix
    
    @property
    def name(self):
        return self._name
    
    @property
    def exists(self):
        return os.path.exists(self._name)
    
    @property
    def destroy(self):
        return self._destroy
    
    def copy(self, destination):
        if self.exists:
            return shutil.copyfile(self.name, destination)
        return False
    
    def do_not_destroy(self):
        self._destroy = False
        return self.name
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.exists and self.destroy:
            if os.path.isfile(self._name):
                os.unlink(self._name)
            elif os.path.isdir(self._name):
                subdirs = []
                for path, dirs, files in os.walk(self._name, followlinks=True):
                    for tf in files:
                        os.unlink(os.path.join(path, tf))
                    subdirs.extend([os.path.join(path, td) for td in dirs])
                for subdir in subdirs:
                    os.rmdir(subdir)


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


# TO LINK A COMPILED GENERATOR AS A DYNAMIC LIBRARY:
#
# clang++ -bundle -undefined dynamic_lookup build/temp.macosx-10.11-x86_64-2.7/hal/api.o 
# build/temp.macosx-10.11-x86_64-2.7/./generators/lesson_15_generators.o 
# build/temp.macosx-10.11-x86_64-2.7/./generators/lesson_16_rgb_generate.o
# -L/usr/local/lib -L/usr/local/opt/openssl/lib -L/usr/local/opt/sqlite/lib
# -o /Users/fish/Dropbox/halogen/hal/api.so -lHalide
#
# ... note that in this case there is unnecessary shit and it should be winnowed down --
#     but this is generally simpler, it is basically this:
#       {CC} {flags} generator.o -o generator.dylib -lHalide -L/where/libDalide/is/at
#     ... where fortunately {flags} are relatively simple, something like e.g.
#     “-bundle -undefined dynamic_lookup” (as above), with possibly an addendum to
#     adjust the @rpath as needed.

if __name__ == '__main__':
    directory = "/Users/fish/Dropbox/halogen/generators"
    outshared = "/tmp/yodogg.dylib"
    with Generators(CONF, outshared, directory) as gens:
        print("IS IT COMPILED? -- %s" % gens.compiled and "YES" or "no")
        print("IS IT LINKED? -- %s" % gens.compiled and "YES" or "no")
    