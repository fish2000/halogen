# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import sysconfig
import ctypes.util

from os.path import splitext
from functools import wraps
from filesystem import back_tick

SHARED_LIBRARY_SUFFIX = splitext(ctypes.util.find_library("c"))[-1]
STATIC_LIBRARY_SUFFIX = ".a"

DEFAULT_VERBOSITY = True

class PythonConfig(object):
    
    """ A config class that provides its values via the output of the command-line
        `python-config` tool (associated with the running Python interpreter). """
    
    # Prefix for the Python installation:
    prefix = '/usr/local'
    
    # Name of the `python-config` binary (nearly always just `python-config`):
    pyconfig = 'python-config'
    
    # The semver-ish name of this Python installation:
    library_name = "python%i.%i" % (sys.version_info.major,
                                    sys.version_info.minor)
    
    # The actual filename for this Python installations’ shared library:
    library_file = "lib%s%s" % (library_name,
                                SHARED_LIBRARY_SUFFIX)
    
    # The actual filename for this Python installations’ base header:
    header_file = 'Python.h'
    
    @classmethod
    def subdirectory(cls, subdir):
        fulldir = os.path.join(cls.prefix, subdir)
        return os.path.isdir(fulldir) and fulldir or None
    
    def __init__(self, cmd=None):
        if not cmd:
            cmd = '%s --prefix' % self.pyconfig
        self.prefix = back_tick(cmd, ret_err=False)
    
    def bin(self):
        return self.subdirectory("bin")
    
    def include(self):
        return self.subdirectory("include")
    
    def lib(self):
        return self.subdirectory("lib")
    
    def libexec(self):
        return self.subdirectory("libexec") or self.lib()
    
    def share(self):
        return self.subdirectory("share")
    
    def Frameworks(self):
        return self.subdirectory("Frameworks")
    
    def Headers(self):
        return self.subdirectory("Headers")
    
    def Resources(self):
        return self.subdirectory("Resources")
    
    def get_includes(self):
        return back_tick("%s --includes" % self.pyconfig)
    
    def get_libs(self):
        return back_tick("%s --libs" % self.pyconfig)
    
    def get_cflags(self):
        return back_tick("%s --cflags" % self.pyconfig)
    
    def get_ldflags(self):
        return back_tick("%s --ldflags" % self.pyconfig)


class BrewedPythonConfig(PythonConfig):
    
    """ A config class that provides its values through calls to the Mac Homebrew
        command-line `brew` tool (with fallback calls to the PythonConfig class). """
    
    def __init__(self, brew_name='python'):
        cmd = "/usr/local/bin/brew --prefix %s" % brew_name
        super(BrewedPythonConfig, self).__init__(cmd)
    
    def include(self):
        for path, dirs, files in os.walk(self.prefix, followlinks=True):
            if self.header_file in files:
                return path
        return super(BrewedPythonConfig, self).include()
    
    def lib(self):
        for path, dirs, files in os.walk(self.prefix, followlinks=True):
            if self.library_file in files:
                return path
        return super(BrewedPythonConfig, self).lib()
    
    def get_includes(self):
        if self.bin():
            return back_tick("%s --includes" % os.path.join(self.bin(), self.pyconfig))
        return super(BrewedPythonConfig, self).get_includes()
    
    def get_libs(self):
        if self.bin():
            return back_tick("%s --libs" % os.path.join(self.bin(), self.pyconfig))
        return super(BrewedPythonConfig, self).get_libs()
    
    def get_cflags(self):
        if self.bin():
            return back_tick("%s --cflags" % os.path.join(self.bin(), self.pyconfig))
        return super(BrewedPythonConfig, self).get_cflags()
    
    def get_ldflags(self):
        if self.bin():
            return back_tick("%s --ldflags" % os.path.join(self.bin(), self.pyconfig))
        return super(BrewedPythonConfig, self).get_ldflags()


def environ_override(name):
    return os.environ.get(name, sysconfig.get_config_var(name) or '')

class SysConfig(PythonConfig):
    
    """ A config class that provides its values using the Python `sysconfig` module
        (with fallback calls to PythonConfig, and environment variable overrides). """
    
    def __init__(self):
        self.prefix = sysconfig.get_path("data")
    
    def bin(self):
        return sysconfig.get_path("scripts")
    
    def include(self):
        return sysconfig.get_path("include")
    
    def lib(self):
        return environ_override('LIBDIR')
    
    def Frameworks(self):
        return environ_override('PYTHONFRAMEWORKPREFIX')
    
    def Headers(self):
        return os.path.join(
            environ_override('PYTHONFRAMEWORKINSTALLDIR'),
            'Headers')
    
    def Resources(self):
        return os.path.join(
            environ_override('PYTHONFRAMEWORKINSTALLDIR'),
            'Resources')
    
    def get_includes(self):
        return "-I%s" % self.include()
    
    def get_libs(self):
        return "-l%s %s" % (self.library_name,
                            environ_override('LIBS'))
    
    def get_cflags(self):
        return "-I%s %s" % (self.include(),
                            environ_override('CFLAGS'))
    
    def get_ldflags(self):
        return "-L%s -l%s %s" % (environ_override('LIBPL'),
                                 self.library_name,
                                 environ_override('LIBS'))


class BrewedConfig(object):
    
    """ A config class that provides its values through calls to the Mac Homebrew
        command-line `brew` tool, for an arbitrary named Homebrew formulae. """
    
    # Name of, and prefix for, the Homebrew installation:
    brew = 'brew'
    prefix = '/usr/local'
    
    # List of cflags to use with all Homebrew-based config classes:
    cflags = frozenset(("-funroll-loops",
                        "-mtune=native",
                        "-O3"))
    
    @classmethod
    def subdirectory(cls, subdir):
        fulldir = os.path.join(cls.prefix, subdir)
        return os.path.isdir(fulldir) and fulldir or None
    
    def __init__(self, brew_name=None):
        if not brew_name:
            brew_name = 'halide'
        self.brew_name = brew_name
        cmd = '/usr/local/bin/%s --prefix %s' % (self.brew, self.brew_name)
        self.prefix = back_tick(cmd, ret_err=False)
    
    def bin(self):
        return self.subdirectory("bin")
    
    def include(self):
        return self.subdirectory("include")
    
    def lib(self):
        return self.subdirectory("lib")
    
    def libexec(self):
        return self.subdirectory("libexec") or self.lib()
    
    def share(self):
        return self.subdirectory("share")
    
    def get_includes(self):
        return "-I%s" % self.include()
    
    def get_libs(self):
        return ""
    
    def get_cflags(self):
        return "-I%s %s" % (self.include(), " ".join(self.cflags))
    
    def get_ldflags(self):
        return "-L%s" % self.lib()


class BrewedHalideConfig(BrewedConfig):
    
    """ A config class that provides its values through calls to the Mac Homebrew
        command-line `brew` tool, specifically pertaining to the Halide formula. """
    
    # Name of the Halide library (sans “lib” prefix and file extension):
    library = "Halide"
    
    # List of Halide-specific cflags to use:
    cflags = frozenset(("-fno-rtti",
                        "-std=c++1z",
                        "-stdlib=libc++")) | BrewedConfig.cflags
    
    def __init__(self):
        super(BrewedHalideConfig, self).__init__(brew_name=self.library.lower())
    
    def get_libs(self):
        return "-l%s" % self.library
    
    def get_ldflags(self):
        return "-L%s -l%s" % (self.lib(), self.library)


class ConfigUnion(object):
    
    """ A config class that provides values as the union of all provided values
        for the arbitrary config classes specified upon construction. E.g.:
            
            config_one = SysConfig()
            config_two = BrewedHalideConfig()
            config_union = ConfigUnion(config_one, config_two)
    """
    
    class union_of(object):
        
        """ Decorator class to abstract the entrails of a ConfigUnion.get_something() function,
            used with function stubs, like so:
            
            class ConfigUnion(object):
            
                @union_of('includes')           # function name without "get_" prefix;
                def get_includes(self, out):    # function definition, specifying `out` set;
                    return out                  # transform the `out` set, if necessary,
                                                # and return it
        """
        
        def __init__(self, name=None):
            """ Initialize the @union_of decorator, stashing the name of the function
                to call upon those config-class instances wrapped by the ConfigUnion
                instance in question. """
            self.name = None
            if name is not None:
                self.name = "get_%s" % str(name)
        
        def __call__(self, base_function):
            """ Process the decorated method, passed in as `base_function` --
                The `base_function` call should process the populated `out` set of flags,
                returning them modified or not. """
            # N.B. the curly-brace expression below is a set comprehension:
            @wraps(base_function)
            def getter(this):
                out = set()
                for config in this.configs:
                    function_to_call = getattr(config, self.name)
                    out |= { x.rstrip() for x in (" %s" % str(" %s" % function_to_call())).split(this.TOKEN) }
                return (this.TOKEN.join(sorted([flag.strip() for flag in base_function(this, out)]))).strip()
            return getter
    
    # WTF HAX
    TOKEN = ' -'
    
    # Ordered list of all possible optimization flags:
    optimization_flags = ["O%s" % str(flag) \
                            for flag in \
                           ('0', 's', 'fast', 'g', '1', '', '2', '3', '4')]
    
    # Set form of optimization flags a la `optimization_flags` above:
    optimization_set = frozenset(optimization_flags)
    
    @classmethod
    def highest_optimization_level(cls, flags):
        """ Strip all but the highest optimization-level compiler flag
            from a set of (de-dashed) flags. Returns a new set. """
        # Which flags are optflags?
        optflags = flags.intersection(cls.optimization_set)
        
        # Exit if the `flags` set contained no optflags:
        if len(optflags) < 1:
            return flags
        
        # Find the optflag with the highest index into cls.optimization.flags:
        flags_index = reduce(lambda x, y: max(x, y),
                          map(lambda flag: cls.optimization_flags.index(flag),
                              optflags))
        
        # Assemble all non-optflags in a new set:
        out = flags - cls.optimization_set
        
        # Append the highest-indexed optflag we found, and return:
        out |= frozenset([cls.optimization_flags[flags_index]])
        return out
    
    def __init__(self, *configs):
        self.configs = list(configs)
    
    @union_of(name='includes')
    def get_includes(self, includes):
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_includes()`: """
        return includes
    
    @union_of(name='libs')
    def get_libs(self, libs):
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_libs()`: """
        return libs
    
    @union_of(name='cflags')
    def get_cflags(self, cflags):
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_cflags()`: """
        # Consolidate optimization flags, passing only the highest flag:
        return self.highest_optimization_level(cflags)
    
    @union_of(name='ldflags')
    def get_ldflags(self, ldflags):
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_ldflags()`: """
        return ldflags


def CC(conf, outfile, infile, verbose=DEFAULT_VERBOSITY):
    """ Execute the C compiler, as named in the `CC` environment variable,
        falling back to the compiler specified in Python `sysconfig`: """
    return back_tick("%s %s -c %s -o %s" % (environ_override('CC'),
                                            conf.get_cflags(),
                                            infile, outfile), ret_err=True, verbose=verbose)

def CXX(conf, outfile, infile, verbose=DEFAULT_VERBOSITY):
    """ Execute the C++ compiler, as named in the `CXX` environment variable,
        falling back to the compiler specified in Python `sysconfig`: """
    return back_tick("%s %s -c %s -o %s" % (environ_override('CXX'),
                                            conf.get_cflags(),
                                            infile, outfile), ret_err=True, verbose=verbose)

def LD(conf, outfile, *infiles, **kwargs):
    """ Execute the dynamic linker, as named in the `LDCXXSHARED` environment variable,
        falling back to the linker specified in Python `sysconfig`: """
    return back_tick("%s %s %s -o %s" % (environ_override('LDCXXSHARED'),
                                         conf.get_ldflags(),
                                         " ".join(infiles), outfile), ret_err=True,
                                                                      verbose=kwargs.pop('verbose', DEFAULT_VERBOSITY))

def AR(conf, outfile, *infiles, **kwargs):
    """ Execute the library archiver, as named in the `AR` environment variable,
        falling back to the compiler specified in Python `sysconfig`: """
    # This function is the ugly duckling here because:
    #   a) it does not use the `conf` arg at all, and
    #   b) it has to manually amend 'ARFLAGS' it would seem
    #       b)[1] ... most configuration-getting pc-configgish flag tools
    #                 could not give less fucks about 'ARFLAGS', and so.
    return back_tick("%s %s %s %s" % (environ_override('AR'),
                                      "%ss" % environ_override('ARFLAGS'),
                                      outfile, " ".join(infiles)), ret_err=True,
                                                                   verbose=kwargs.pop('verbose', DEFAULT_VERBOSITY))

test_generator_source = """
#include "Halide.h"
#include <stdio.h>
using namespace Halide;

class MyFirstGenerator : public Halide::Generator<MyFirstGenerator> {
    public:
        Param<uint8_t> offset{"offset"};
        ImageParam input{UInt(8), 2, "input"};
        Var x, y;
        Func build() {
            Func brighter;
            brighter(x, y) = input(x, y) + offset;
            brighter.vectorize(x, 16).parallel(y);
            return brighter;
        }
};

RegisterGenerator<MyFirstGenerator> my_first_generator{"my_first_generator"};
"""

if __name__ == '__main__':
    from utils import print_config, test_compile, terminal_width
    
    brewedHalideConfig = BrewedHalideConfig()
    sysConfig = SysConfig()
    brewedPythonConfig = BrewedPythonConfig()
    pythonConfig = PythonConfig()
    
    configUnion = ConfigUnion(brewedHalideConfig, sysConfig)
    configUnionAll = ConfigUnion(brewedHalideConfig, sysConfig,
                                 brewedPythonConfig, pythonConfig)
    
    
    """ Test basic config methods: """
    
    print("")
    print("TESTING: BrewedHalideConfig ...")
    print("")
    print_config(brewedHalideConfig)
    
    print("=" * terminal_width)
    print("")
    print("TESTING: SysConfig ...")
    print("")
    print_config(sysConfig)
    
    print("=" * terminal_width)
    print("")
    print("TESTING: BrewedPythonConfig ...")
    print("")
    print_config(brewedPythonConfig)
    
    print("=" * terminal_width)
    print("")
    print("TESTING: PythonConfig ...")
    print("")
    print_config(pythonConfig)
    
    print("=" * terminal_width)
    print("")
    print("TESTING: ConfigUnion<BrewedHalideConfig, SysConfig> ...")
    print("")
    print_config(configUnion)
    
    print("=" * terminal_width)
    print("")
    print("TESTING: ConfigUnion<BrewedHalideConfig, SysConfig, BrewedPythonConfig, PythonConfig> ...")
    print("")
    print_config(configUnionAll)
    
    """ Test compilation with different configs: """
    
    print("=" * terminal_width)
    print("")
    print("TEST COMPILATION: CXX(brewedHalideConfig, <out>, <in>) ...")
    print("")
    test_compile(brewedHalideConfig, test_generator_source)
    
    print("=" * terminal_width)
    print("")
    print("TEST COMPILATION: CXX(configUnion, <out>, <in>) ...")
    print("")
    test_compile(configUnion, test_generator_source)
    
    print("=" * terminal_width)
    print("")
    print("TEST COMPILATION: CXX(configUnionAll, <out>, <in>) ...")
    print("")
    test_compile(configUnionAll, test_generator_source)
    
    
    
