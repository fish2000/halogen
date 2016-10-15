# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import sysconfig

import ctypes.util
from os.path import splitext
from filesystem import back_tick

SHARED_LIBRARY_SUFFIX = splitext(ctypes.util.find_library("c"))[-1]
STATIC_LIBRARY_SUFFIX = ".a"

class PythonConfig(object):
    
    prefix = '/usr/local'
    pyconfig = 'python-config'
    
    library_name = "python%i.%i" % (sys.version_info.major,
                                    sys.version_info.minor)
    
    library_file = "lib%s%s" % (library_name,
                                SHARED_LIBRARY_SUFFIX)
    
    header_file = 'Python.h'
    
    def __init__(self, cmd=None):
        if not cmd:
            cmd = '%s --prefix' % self.pyconfig
        self.prefix = back_tick(cmd, ret_err=False)
    
    def subdirectory(self, subdir):
        fulldir = os.path.join(self.prefix, subdir)
        return os.path.isdir(fulldir) and fulldir or None
    
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
    
    def __init__(self, brew_name='python'):
        cmd = "brew --prefix %s" % brew_name
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
    
    brew = 'brew'
    prefix = '/usr/local'
    
    cflags = frozenset(("-funroll-loops",
                        "-mtune=native",
                        "-O3"))
    
    def __init__(self, brew_name=None):
        if not brew_name:
            brew_name = 'halide'
        self.brew_name = brew_name
        cmd = '%s --prefix %s' % (self.brew, self.brew_name)
        self.prefix = back_tick(cmd, ret_err=False)
    
    def subdirectory(self, subdir):
        fulldir = os.path.join(self.prefix, subdir)
        return os.path.isdir(fulldir) and fulldir or None
    
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
    
    library = "Halide"
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
    
    """ WTF HAX """
    TOKEN = ' -'
    
    def __init__(self, *configs):
        self.configs = list(configs)
    
    def get_includes(self):
        out = set()
        for config in self.configs:
            out |= set((" %s" % config.get_includes()).split(self.TOKEN))
        return (self.TOKEN.join(sorted([flag.strip() for flag in out]))).strip()
    
    def get_libs(self):
        out = set()
        for config in self.configs:
            out |= set((" %s" % config.get_libs()).split(self.TOKEN))
        return (self.TOKEN.join(sorted([flag.strip() for flag in out]))).strip()
    
    def get_cflags(self):
        out = set()
        for config in self.configs:
            out |= set((" %s" % config.get_cflags()).split(self.TOKEN))
        return (self.TOKEN.join(sorted([flag.strip() for flag in out]))).strip()
    
    def get_ldflags(self):
        out = set()
        for config in self.configs:
            out |= set((" %s" % config.get_ldflags()).split(self.TOKEN))
        return (self.TOKEN.join(sorted([flag.strip() for flag in out]))).strip()


def CC(conf, outfile, infile, verbose=False):
    return back_tick("%s %s -c %s -o %s" % (environ_override('CC'),
                                            conf.get_cflags(),
                                            infile, outfile), ret_err=True, verbose=verbose)

def CXX(conf, outfile, infile, verbose=False):
    return back_tick("%s %s -c %s -o %s" % (environ_override('CXX'),
                                            conf.get_cflags(),
                                            infile, outfile), ret_err=True, verbose=verbose)

def LD(conf, outfile, *infiles, **kwargs):
    return back_tick("%s %s %s -o %s" % (environ_override('LDCXXSHARED'),
                                         conf.get_ldflags(),
                                         " ".join(infiles), outfile), ret_err=True,
                                                                      verbose=kwargs.pop('verbose', False))

def AR(conf, outfile, *infiles, **kwargs):
    # This function is the ugly duckling here because:
    #   a) it does not use the `conf` arg at all, and
    #   b) it has to manually amend 'ARFLAGS' it would seem
    #       b)[1] ... most configuration-getting pc-configgish flag tools
    #                 could not give less fucks about 'ARFLAGS', and so.
    return back_tick("%s %s %s %s" % (environ_override('AR'),
                                      "%ss" % environ_override('ARFLAGS'),
                                      outfile, " ".join(infiles)), ret_err=True,
                                                                   verbose=kwargs.pop('verbose', False))

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
    
    HORIZONTAL_RULE_WIDTH = 120
    
    def print_config(conf):
        print("INCLUDES:")
        print("")
        print(conf.get_includes())
        print("")
        print("-" * HORIZONTAL_RULE_WIDTH)
        
        print("LIBS:")
        print("")
        print(conf.get_libs())
        print("")
        print("-" * HORIZONTAL_RULE_WIDTH)
        
        print("CFLAGS:")
        print("")
        print(conf.get_cflags())
        print("")
        print("-" * HORIZONTAL_RULE_WIDTH)
        
        print("LDFLAGS:")
        print("")
        print(conf.get_ldflags())
        print("")
        # print("-" * HORIZONTAL_RULE_WIDTH)
        
    
    def test_compile(conf):
        # import shutil
        from tempfile import NamedTemporaryFile, mktemp
        output = tuple()
        px = "yodogg-"
        with NamedTemporaryFile(suffix=".cpp", prefix=px) as tf:
            tf.file.write(test_generator_source)
            tf.file.flush()
            adotout = mktemp(suffix=".cpp.o", prefix=px)
            
            print("C++ SOURCE: %s" % tf.name)
            print("C++ TARGET: %s" % adotout)
            
            output += CXX(conf, adotout, tf.name, verbose=True)
            
            print("-" * HORIZONTAL_RULE_WIDTH)
            
            if len(output[1]) > 0:
                # failure
                print("COMPILATION FAILED:")
                print(output[0], file=sys.stdout)
                print(output[1], file=sys.stderr)
                if os.path.exists(adotout):
                    os.unlink(adotout)
                return
            
            # success!
            print("COMPILATION TOTALLY WORKED!")
            print(output[0], file=sys.stdout)
            print(output[1], file=sys.stderr)
            if os.path.exists(adotout):
                # another = os.path.basename(mktemp(suffix=".cpp.o", prefix=px))
                # shutil.copy2(adotout, "/tmp/%s" % another)
                os.unlink(adotout)
            else:
                print("... BUT THEN WHERE THE FUCK IS MY SHIT?!?!")
    
    brewedHalideConfig = BrewedHalideConfig()
    sysConfig = SysConfig()
    brewedPythonConfig = BrewedPythonConfig()
    pythonConfig = PythonConfig()
    
    configUnion = ConfigUnion(brewedHalideConfig, sysConfig)
    
    # print("=" * HORIZONTAL_RULE_WIDTH)
    print("")
    print("TESTING: BrewedHalideConfig ...")
    print("")
    print_config(brewedHalideConfig)
    
    print("=" * HORIZONTAL_RULE_WIDTH)
    print("")
    print("TESTING: SysConfig ...")
    print("")
    print_config(sysConfig)
    
    print("=" * HORIZONTAL_RULE_WIDTH)
    print("")
    print("TESTING: BrewedPythonConfig ...")
    print("")
    print_config(brewedPythonConfig)
    
    print("=" * HORIZONTAL_RULE_WIDTH)
    print("")
    print("TESTING: PythonConfig ...")
    print("")
    print_config(pythonConfig)
    
    print("=" * HORIZONTAL_RULE_WIDTH)
    print("")
    print("TESTING: ConfigUnion<BrewedHalideConfig, SysConfig> ...")
    print("")
    print_config(configUnion)
    
    print("=" * HORIZONTAL_RULE_WIDTH)
    print("")
    print("TEST COMPILATION: CXX(configUnion, <out>, <in>) ...")
    print("")
    test_compile(brewedHalideConfig)
    
    
    
