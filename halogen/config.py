# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import re
import sys
import sysconfig
import six

try:
    from scandir import walk
except ImportError:
    from os import walk

try:
    from functools import reduce
except ImportError:
    pass

from abc import ABC, ABCMeta, abstractmethod
from os.path import splitext
from ctypes.util import find_library
from functools import wraps
from filesystem import which, back_tick, script_path
from utils import stringify, u8bytes, u8str

__all__ = ('SHARED_LIBRARY_SUFFIX',
           'STATIC_LIBRARY_SUFFIX',
           'DEFAULT_VERBOSITY', 'TOKEN',
           'ConfigSubBase', 'ConfigBaseMeta', 'ConfigBase',
           'PythonConfig',
           'BrewedPythonConfig',
           'environ_override',
           'SysConfig', 'PkgConfig', 'BrewedConfig',
                                     'BrewedHalideConfig',
                                     'BrewedImreadConfig',
           'ConfigUnion',
           'CC', 'CXX', 'LD', 'AR',
           'main', 'corefoundation_check')

SHARED_LIBRARY_SUFFIX = splitext(find_library("c"))[-1].lower()
STATIC_LIBRARY_SUFFIX = (SHARED_LIBRARY_SUFFIX == ".dll") and ".lib" or ".a"

DEFAULT_VERBOSITY = True

# WTF HAX
TOKEN = ' -'

SubBaseAncestor = six.with_metaclass(ABCMeta, ABC)
class ConfigSubBase(SubBaseAncestor):
    
    """ The abstract base class ancestor of all Config-ish classes we define here.
        
        By “Config-ish class” I mean, a class we can use as a Config instance when
        instantiated – and in the Pythonic duck-typology sense of things, all that
        means is that the class has maybe four basic methods: `get_includes()`,
        `get_libs()`, `get_cflags()`, and `get_ldflags()`. Like, if your class
        implements these and the instance methods do what they look like they should
        do, you can e.g. pass that instance to our CC, CXX, LD, or AR functions (which
        are defined below) or, say, use that instance in the construction of a working
        ConfigUnion instance, or what have you.
        
        (In fact, you may be able to get away with only implementing `get_cflags()` and
        `get_ldflags()` – those are the only methods explicitly called by CC/CXX/LD;
        AR doesn’t even use its config-instance parameter at the moment.)
        
        You don’t strictly need to inherit from ConfigSubBase – in fact, that is unwise;
        I recommend inheriting from ConfigBase (q.v. class definition sub.) as that will
        get you all of the goodies like FieldList inheritance, the “prefix” property and
        the “subdirectory()” method, and other stuff you can read about below.
    """
    
    base_field_cache = {}
    
    # Prefix get/set/delete methods:
    
    @property
    @abstractmethod
    def prefix(self): pass
    
    @prefix.setter
    @abstractmethod
    def prefix(self, value): pass
    
    @prefix.deleter
    @abstractmethod
    def prefix(self): pass
    
    # The subdirectory method is used throughout
    # all Config subclasses:
    
    @abstractmethod
    def subdirectory(self, subdir, whence=None): pass
    
    # Stringification and representation methods:
    
    @abstractmethod
    def to_string(self, field_list=None): pass
    
    @abstractmethod
    def __repr__(self): pass
    
    @abstractmethod
    def __str__(self): pass
    
    @abstractmethod
    def __bytes__(self): pass
    
    @abstractmethod
    def __unicode__(self): pass
    
    # These four get_* methods make up the bare-bones
    # requirement for what a Config subclass needs
    # to provide:
    
    @abstractmethod
    def get_includes(self): pass
    
    @abstractmethod
    def get_libs(self): pass
    
    @abstractmethod
    def get_cflags(self): pass
    
    @abstractmethod
    def get_ldflags(self): pass


class ConfigBaseMeta(ABCMeta):
    
    """ The metaclass for all Config-ish classes we define here; used with
        ConfigBase (q.v. class definition sub.)
    """
    
    def __new__(cls, name, bases, attributes):
        if not 'base_fields' in attributes:
            attributes['base_fields'] = tuple()
        base_fields = set(attributes['base_fields'])
        for base in bases:
            if hasattr(base, 'base_fields'):
                base_fields |= frozenset(base.base_fields)
            if hasattr(base, 'fields'):
                base_fields |= frozenset(base.fields)
        attributes['base_fields'] = tuple(sorted(base_fields))
        ConfigSubBase.base_field_cache[name] = tuple(sorted(base_fields))
        outcls = ABCMeta.__new__(cls, name, bases, attributes)
        ConfigSubBase.register(outcls)
        return outcls


BaseAncestor = six.with_metaclass(ConfigBaseMeta, ConfigSubBase)
class ConfigBase(BaseAncestor):
    
    """ The base class for all Config-ish classes we define here. This includes:
        
        * The list of “base fields” and “dir(ectory) fields” -- see the docstring
          below for the inner FieldList class for how these are used.
        * The definition of the “prefix” property, a property that pretty much all
          of our Config-ish subclasses rely on (with the notable exception of the 
          ConfigUnion class, q.v. class definition sub.)
        * The definition of the “subdirectory(…)” method, which is also very popular
          with the subclasses.
        * Definitions for __repr__(), __str__(), __unicode__(), and a “to_string(…)”
          method -- all of which should be adequate for, like, 99 percent of all of
          the possible subclasses’ introspection-printing needs; also see docstrings
          and definitions below of FieldList for related internals.
    """
    
    base_fields = ('prefix', 'get_includes',
                             'get_libs',
                             'get_cflags',
                             'get_ldflags')
    
    dir_fields = ('bin', 'include',
                  'lib', 'libexec', 'libexecbin',
                  'share')
    
    class FieldList(object):
        
        """ This class enables a sort-of inheritance scheme for the “fields” attribute.
            The “stringify(…)” function, typically used in __repr__() and __str__() methods,
            uses the “fields” attribute (an iterable of strings) to determine what fields of
            the instance to introspect in order to print. By assigning a FieldList instance
            to “fields” on classes whose metaclass is ConfigBaseMeta (q.v. class definition
            supra), each FieldList builds its list of fields using the class ancestors’
            FieldLists as well as the current class.
            
            This is accomplished by FieldList, which follows the descriptor protocol and thus
            has __set__() and __get__() methods governing what happens when a FieldList is
            accessed as an instance attribute, uses set logic to sum the names of all the
            relevant ancestor fields with those with which it was defined before returning
            a value.
            
            Does that make sense? I hope it makes some sense. If not, read the code and get
            back to me if you are still confused. Thanks! -Alex
        """
        
        __slots__ = ('stored_fields', 'more_fields',
                                      'exclude_fields',
                                      'include_dir_fields')
        
        def __init__(self, *more_fields, **kwargs):
            self.include_dir_fields = kwargs.pop('dir_fields', False)
            self.exclude_fields = frozenset(kwargs.pop('exclude', tuple()))
            self.more_fields = frozenset(more_fields)
            if self.include_dir_fields:
                self.stored_fields = self.more_fields | frozenset(ConfigBase.dir_fields)
            else:
                self.stored_fields = self.more_fields
        
        def __get__(self, instance, cls=None):
            if cls is None:
                cls = type(instance)
            out = set(self.stored_fields)
            if hasattr(cls, 'base_fields'):
                out |= frozenset(cls.base_fields)
            out -= self.exclude_fields
            return tuple(sorted(out))
        
        def __set__(self, instance, value):
            self.more_fields = frozenset(value)
            if self.include_dir_fields:
                self.stored_fields = self.more_fields | frozenset(ConfigBase.dir_fields)
            else:
                self.stored_fields = self.more_fields
        
        def __delete__(self, instance):
            raise AttributeError("Can't delete a FieldList attribute")
    
    @property
    def prefix(self):
        """ The path to the Python installation prefix """
        if not hasattr(self, '_prefix'):
            self._prefix = sys.prefix
        return getattr(self, '_prefix')
    
    @prefix.setter
    def prefix(self, value):
        if not os.path.exists(value):
            raise ValueError("prefix path does not exist: %s" % value)
        self._prefix = value
    
    @prefix.deleter
    def prefix(self):
        if hasattr(self, '_prefix'):
            del self._prefix
    
    def subdirectory(self, subdir, whence=None):
        """ Returns the path to a subdirectory within this Config instances’ prefix """
        if not whence:
            whence = getattr(self, '_prefix', sys.prefix)
        fulldir = os.path.join(whence, subdir)
        return os.path.exists(fulldir) and fulldir or None
    
    def to_string(self, field_list=None):
        """ Stringify the instance, using either a provided list of fields to evaluate,
            or if none was provided, the iterable-of-strings class variable “fields”.
        """
        if not field_list:
            field_list = self.__class__.fields
        return stringify(self, field_list)
    
    def __repr__(self):
        return stringify(self, self.__class__.fields)
    
    def __str__(self):
        return stringify(self, self.__class__.fields)
    
    def __bytes__(self):
        return u8bytes(repr(self))
    
    def __unicode__(self):
        return six.u(repr(self))


class Macro(object):
    
    __slots__ = ('name', 'definition')
    
    def __init__(self, name, definition=None):
        self.name = name
        self.definition = definition
    
    def to_string(self):
        if self.definition is not None:
            return "-D%s=%s" % (u8str(self.name),
                                u8str(self.definition))
        return "-D%s" % u8str(self.name)
    
    def to_tuple(self):
        if self.definition is not None:
            return (u8str(self.name),
                    u8str(self.definition))
        return (u8str(self.name), '')
    
    def __repr__(self):
        return stringify(self, self.__class__.__slots__)
    
    def __str__(self):
        return self.to_string()
    
    def __bytes__(self):
        return u8bytes(self.to_string())
    
    def __unicode__(self):
        return six.u(self.to_string())


class Macros(dict):
    
    def define(self, name, definition=None):
        if name in self:
            raise ValueError("Macro %s already defined: %s" % (name, self[name]))
        self[name] = definition
        return Macro(name, definition)
    
    def undefine(self, name, **kwargs):
        if name in self:
            del self[name]
    
    def add(self, macro):
        return self.define(macro.name,
                           macro.definition)
    
    def defined_as(self, name):
        if name not in self:
            return None
        return Macro(name, self[name])
    
    def to_tuple(self):
        out = tuple()
        for k, v in self.items():
            out += ((k, v),)
        return out
    
    def to_string(self):
        return " ".join(Macro(k, v).to_string() for k, v in self.items())
    
    def __str__(self):
        return self.to_string()
    
    def __bytes__(self):
        return u8bytes(self.to_string())
    
    def __unicode__(self):
        return six.u(self.to_string())
    

class PythonConfig(ConfigBase):
    
    """ A config class that provides its values via the output of the command-line
        `python-config` tool (associated with the running Python interpreter).
    """
    
    # 'Headers', 'Resources', 'framework'
    
    fields = ConfigBase.FieldList('pyconfig', 'pyconfigpath',
                                  'library_name', 'library_file', 'header_file',
                                  'framework_name', 'framework_path',
                                  'Frameworks',
                                   dir_fields=False)
    
    # Name of the `python-config` binary (nearly always just `python-config`):
    pyconfig = "python-config"
    pyconfigpath = which(pyconfig)
    
    # The semver-ish name of this Python installation:
    library_name = "python%i.%i" % (sys.version_info.major,
                                    sys.version_info.minor)
    
    # The actual filename for this Python installations’ shared library:
    library_file = "lib%s%s" % (library_name,
                                SHARED_LIBRARY_SUFFIX)
    
    # The actual filename for this Python installations’ base header:
    header_file = 'Python.h'
    
    # The name of the framework for this python installation:
    framework_name = 'Python.framework'
    
    # the path to the 'Frameworks' directory (empty before calls):
    framework_path = None
    
    def __init__(self, prefix=None):
        """ Initialize PythonConfig, optionally specifying a system prefix """
        if not prefix:
            prefix = str(sys.prefix)
        self.prefix = prefix
    
    def bin(self):
        return self.subdirectory("bin")
    
    def include(self):
        return self.subdirectory("include")
    
    def lib(self):
        return self.subdirectory("lib")
    
    def libexec(self):
        return self.subdirectory("libexec") or self.lib()
    
    def libexecbin(self):
        return self.subdirectory('bin', whence=self.subdirectory("libexec"))
    
    def share(self):
        return self.subdirectory("share")
    
    def Frameworks(self):
        if not self.framework_path:
            # from prefix, search depth-first up (linear):
            if self.framework_name in self.prefix:
                head = self.prefix
                tail = "yo dogg" # something not false-y
                while tail:
                    head, tail = os.path.split(head)
                    if tail == self.framework_name:
                        self.framework_path = head
                        return self.framework_path
            # from prefix, search depth-first down (likely exponential):
            for path, dirs, files in walk(self.prefix, followlinks=True):
                if self.framework_name in dirs:
                    self.framework_path = path
                    return self.framework_path
            # give up, using a sensible default:
            self.framework_path = self.subdirectory('Frameworks')
        return self.framework_path
    
    def Headers(self):
        return self.subdirectory('Headers',
                                  whence=os.path.join(self.framework_path,
                                                      self.framework_name))
    
    def Resources(self):
        return self.subdirectory('Resources',
                                  whence=os.path.join(self.framework_path,
                                                      self.framework_name))
    
    def framework(self):
        return self.subdirectory(self.framework_name, self.framework_path)
    
    def get_includes(self):
        return back_tick("%s --includes" % self.pyconfigpath)
    
    def get_libs(self):
        return back_tick("%s --libs" % self.pyconfigpath)
    
    def get_cflags(self):
        return back_tick("%s --cflags" % self.pyconfigpath)
    
    def get_ldflags(self):
        return back_tick("%s --ldflags" % self.pyconfigpath)


class BrewedPythonConfig(PythonConfig):
    
    """ A config class that provides its values through calls to the Mac Homebrew
        command-line `brew` tool (with fallback calls to the PythonConfig class).
    """
    
    fields = ConfigBase.FieldList('brew',
                                  'brew_name', dir_fields=True)
    
    # Path to the Homebrew executable CLT `brew`
    brew = which("brew")
    
    def __init__(self, brew_name=None):
        """ Initialize BrewedPythonConfig, optionally naming a homebrew formula """
        if not self.brew:
            raise IOError("Can't find Homebrew “brew” executable")
        if not brew_name:
            brew_name = 'python'
        self.brew_name = brew_name
        cmd = "%s --prefix %s" % (self.brew, self.brew_name)
        prefix = back_tick(cmd, ret_err=False)
        super(BrewedPythonConfig, self).__init__(prefix=prefix)
    
    def include(self):
        for path, dirs, files in walk(self.prefix, followlinks=True):
            if self.header_file in files:
                return path
        return super(BrewedPythonConfig, self).include()
    
    def lib(self):
        for path, dirs, files in walk(self.prefix, followlinks=True):
            if self.library_file in files:
                return path
        return super(BrewedPythonConfig, self).lib()


def environ_override(name):
    return os.environ.get(name, sysconfig.get_config_var(name) or '')

class SysConfig(PythonConfig):
    
    fields = ConfigBase.FieldList(dir_fields=True)
    
    """ A config class that provides its values using the Python `sysconfig` module
        (with fallback calls to PythonConfig, and environment variable overrides).
    """
    
    def __init__(self):
        """ Initialize SysConfig, optionally specifying a system path """
        prefix = sysconfig.get_path("data")
        super(SysConfig, self).__init__(prefix=prefix)
    
    def bin(self):
        return sysconfig.get_path("scripts")
    
    def include(self):
        return sysconfig.get_path("include")
    
    def lib(self):
        return environ_override('LIBDIR')
    
    def Frameworks(self):
        return environ_override('PYTHONFRAMEWORKPREFIX')
    
    def Headers(self):
        return self.subdirectory('Headers',
                                  whence=environ_override('PYTHONFRAMEWORKINSTALLDIR'))
    
    def Resources(self):
        return self.subdirectory('Resources',
                                  whence=environ_override('PYTHONFRAMEWORKINSTALLDIR'))
    
    def get_includes(self):
        return "-I%s" % self.include()
    
    def get_libs(self):
        return "-l%s %s" % (self.library_name,
                            environ_override('LIBS'))
    
    def get_cflags(self):
        out = "-I%s %s %s" % (self.include(),
                              environ_override('CFLAGS'),
                              environ_override('CXXFLAGS'))
        return out.rstrip()
    
    def get_ldflags(self):
        ldstring = ""
        libpths = (environ_override('LIBDIR'),
                   environ_override('LIBPL'),
                   environ_override('LIBDEST'))
        for pth in libpths:
            if os.path.exists(pth):
                ldstring += " -L%s" % pth
        out = "%s -l%s %s" % (ldstring.lstrip(),
                              self.library_name,
                              environ_override('LIBS'))
        return out.lstrip()


class PkgConfig(ConfigBase):
    
    """ A config class that provides its values using the `pkg-config`
        command-line tool, for a package name recognized by same.
    """
    
    fields = ConfigBase.FieldList('cflags',
                                  'pkgconfig',
                                  'pkg_name', dir_fields=True)
    
    # List of cflags to use with all pkg-config-based classes:
    cflags = frozenset(("-funroll-loops",
                        "-mtune=native",
                        "-O3"))
    
    # Location of the `pkg-config` binary:
    pkgconfig = which('pkg-config')
    
    # Cache of complete package list:
    packages = set()
    did_load_packages = False
    
    @classmethod
    def load_packages(cls):
        """ Load all package names from `pkg-config` """
        if not cls.did_load_packages:
            from errors import ExecutionError
            script = which('all-pkgconfig-packages.sh', pathvar=script_path())
            try:
                cls.packages |= frozenset(back_tick(script).split('\n'))
            except ExecutionError:
                cls.did_load_packages = False
            else:
                cls.did_load_packages = True
        return len(cls.packages)
    
    @classmethod
    def add_package(cls, pkg_name):
        """ Add a package name to the set of all package names """
        cls.packages |= { pkg_name }
    
    @classmethod
    def check_package(cls, pkg_name):
        """ Check a package name for validity against the loaded set of names """
        return pkg_name in cls.packages
    
    def __init__(self, pkg_name=None):
        """ Initialize PkgConfig, optionally naming a package (the default is “python3”) """
        if not pkg_name:
            pkg_name = 'python3'
        self.pkg_name = pkg_name
        self.add_package(pkg_name)
        self.prefix = back_tick("%s %s --variable=prefix" % (self.pkgconfig,
                                                             self.pkg_name),
                                                             ret_err=False)
    
    def bin(self):
        return self.subdirectory("bin")
    
    def include(self):
        return self.subdirectory("include")
    
    def lib(self):
        return self.subdirectory("lib")
    
    def libexec(self):
        return self.subdirectory("libexec") or self.lib()
    
    def libexecbin(self):
        return self.subdirectory('bin', whence=self.subdirectory('libexec'))
    
    def share(self):
        return self.subdirectory("share")
    
    def get_includes(self):
        return back_tick("%s %s --cflags-only-I" % (self.pkgconfig,
                                                    self.pkg_name),
                                                    ret_err=False)
    
    def get_libs(self):
        return back_tick("%s %s --libs-only-l --libs-only-other --static" % (self.pkgconfig,
                                                                             self.pkg_name),
                                                                             ret_err=False)
    
    def get_cflags(self):
        return "%s %s" % (" ".join(self.cflags),
                          back_tick("%s %s --cflags" % (self.pkgconfig,
                                                        self.pkg_name),
                                                        ret_err=False))
    
    def get_ldflags(self):
        return back_tick("%s %s --libs --static" % (self.pkgconfig,
                                                    self.pkg_name),
                                                    ret_err=False)


class NumpyConfig(ConfigBase):
    
    subpackages = ('npymath', 'mlib')
    
    fields = ConfigBase.FieldList('subpackages',
                                  'info', 'macros',
                                  'get_numpy_include_directory',
                                  'include', 'lib', dir_fields=False)
    
    @classmethod
    def get_numpy_include_directory(cls):
        if not hasattr(cls, 'include_path'):
            import numpy
            cls.include_path = numpy.get_include()
        return cls.include_path
    
    def __init__(self):
        """ Prefix is likely /…/numpy/core """
        self.info = {}
        self.macros = Macros()
        self.prefix = os.path.dirname(self.get_numpy_include_directory())
        import numpy.distutils, numpy.version
        for package in self.subpackages:
            infodict = numpy.distutils.misc_util.get_info(package)
            for k, v in infodict.items():
                if not k in self.info:
                    self.info[k] = set()
                self.info[k] |= set(v)
        self.info['include_dirs'] |= { self.get_numpy_include_directory() }
        self.macros.define('NUMPY_VERSION',             '\\"%s\\"' % numpy.version.version)
        self.macros.define('NPY_NO_DEPRECATED_API',     'NPY_1_7_API_VERSION')
        self.macros.define('PY_ARRAY_UNIQUE_SYMBOL',    'YO_DOGG_I_HEARD_YOU_LIKE_UNIQUE_SYMBOLS')
    
    def include(self):
        return self.subdirectory("include")
    
    def lib(self):
        return self.subdirectory("lib")
    
    def get_includes(self):
        return " ".join("-I%s" % include_dir for include_dir \
                            in sorted(self.info['include_dirs']))
    
    def get_libs(self):
        return " ".join("-l%s" % library for library \
                        in sorted(self.info['libraries']))
    
    def get_cflags(self):
        return "%s %s" % (self.get_includes(),
                          self.macros.to_string())
    
    def get_ldflags(self):
        return "%s %s" % (" ".join("-L%s" % library_dir for library_dir \
                                       in sorted(self.info['library_dirs'])),
                          self.get_libs())

class BrewedConfig(ConfigBase):
    
    """ A config class that provides its values through calls to the Mac Homebrew
        command-line `brew` tool, for arbitrary named Homebrew formulae.
    """
    
    fields = ConfigBase.FieldList('brew',
                                  'brew_name',
                                  'cflags', dir_fields=False)
    
    # Name of, and prefix for, the Homebrew installation:
    brew = which('brew')
    
    # List of cflags to use with all Homebrew-based config classes:
    cflags = frozenset(("-funroll-loops",
                        "-mtune=native",
                        "-O3"))
    
    def __init__(self, brew_name=None):
        """ Initialize BrewedConfig, optionally naming a formula (the default is “halide”) """
        if not brew_name:
            brew_name = 'halide'
        self.brew_name = brew_name
        cmd = '%s --prefix %s' % (self.brew, self.brew_name)
        self.prefix = back_tick(cmd, ret_err=False)
    
    def bin(self):
        return self.subdirectory("bin")
    
    def include(self):
        return self.subdirectory("include")
    
    def lib(self):
        return self.subdirectory("lib")
    
    def libexec(self):
        return self.subdirectory("libexec") or self.lib()
    
    def libexecbin(self):
        return self.subdirectory('bin', whence=self.subdirectory('libexec'))
    
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
        command-line `brew` tool, specifically pertaining to the Halide formula.
    """
    
    fields = ConfigBase.FieldList('library', dir_fields=True)
    
    # Name of the Halide library (sans “lib” prefix and file extension):
    library = "Halide"
    
    # List of Halide-specific cflags to use:
    cflags = frozenset(("-fno-rtti",
                        "-std=c++1z",
                        "-stdlib=libc++")) | BrewedConfig.cflags
    
    def __init__(self):
        """ Initialize BrewedHalideConfig (constructor takes no arguments) """
        super(BrewedHalideConfig, self).__init__(brew_name=self.library.lower())
    
    def get_libs(self):
        return "-l%s" % self.library
    
    def get_ldflags(self):
        return "-L%s -l%s" % (self.lib(), self.library)


class BrewedImreadConfig(BrewedConfig):
    
    """ A config class that provides its values through calls to the Mac Homebrew
        command-line `brew` tool, specifically pertaining to the “libimread” formula.
    """
    
    fields = ConfigBase.FieldList('library',
                                  'config_command', dir_fields=True)
    
    # Name of the libimread library (sans “lib” prefix and file extension):
    library = "imread"
    
    def __init__(self, brew_name=None):
        """ Complete override of BrewedConfig’s __init__ method: """
        if not brew_name:
            brew_name = 'libimread'
        self.brew_name = brew_name
        self.config_command = which('imread-config')
        cmd = '%s --prefix' % self.config_command
        self.prefix = back_tick(cmd, ret_err=False)
    
    def get_includes(self):
        return back_tick("%s --includes" % self.config_command,
                                           ret_err=False)
    
    def get_libs(self):
        return back_tick("%s --libs" % self.config_command,
                                       ret_err=False)
    
    def get_cflags(self):
        return back_tick("%s --cflags" % self.config_command,
                                         ret_err=False)
    
    def get_ldflags(self):
        return back_tick("%s --ldflags" % self.config_command,
                                          ret_err=False)


class ConfigUnion(ConfigBase):
    
    """ A config class that provides values as the union of all provided values
        for the arbitrary config classes specified upon construction. E.g.:
            
            config_one = SysConfig()
            config_two = BrewedHalideConfig()
            config_union = ConfigUnion(config_one, config_two)
    """
    
    # Unlike most Config-ish classes, “prefix” is irrelevant for ConfigUnions.
    fields = ConfigBase.FieldList('sub_config_types', exclude=['prefix'],
                                                      dir_fields=False)
    
    class union_of(object):
        
        """ Decorator class to abstract the entrails of a ConfigUnion.get_something() function,
            used with function stubs, like so:
            
            class ConfigUnion(ConfigBase):
            
                @union_of('includes')           # function name without "get_" prefix;
                def get_includes(self, out):    # function definition, specifying `out` set;
                    return out                  # transform the `out` set, if necessary,
                                                # and return it
        """
        
        __slots__ = ('name',)
        
        def __init__(self, name):
            """ Initialize the @union_of decorator, stashing the name of the function
                to call upon those config-class instances wrapped by the ConfigUnion
                instance in question. """
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
                    out |= { flag.strip() for flag in (" %s" % function_to_call()).split(TOKEN) }
                return (TOKEN.join(sorted(base_function(this, out)))).strip()
            return getter
    
    class FlagSet(object):
        
        """ A sugary-sweet class for stowing a set of flags whose order is significant. """
        
        joiner = ", %s" % TOKEN.lstrip()
        __slots__ = ('flags', 'set')
        
        def __init__(self, template, flaglist):
            self.flags = [template % flag for flag in flaglist]
            self.set = frozenset(self.flags)
        
        def __contains__(self, rhs):
            return rhs in self.set
        
        def __len__(self):
            return len(self.set)
        
        def __getitem__(self, key):
            return self.flags[key]
        
        def index(self, value):
            return self.flags.index(value)
        
        def __repr__(self):
            return "[%s%s ]" % (TOKEN, self.joiner.join(self.flags))
        
        def __str__(self):
            return "[%s%s ]" % (TOKEN, self.joiner.join(self.flags))
        
        def __bytes__(self):
            return u8bytes(repr(self))
        
        def __unicode__(self):
            return six.u(str(self))
    
    # Ordered list of all possible optimization flags:
    optimization = FlagSet("O%s", ('0', 's', 'fast', '1',
                                   'g', '',  '2',    '3',
                                   '4')) # 4 is technically a fake
    
    # Regular expression to match fake optimization flags e.g. -O8, -O785 etc.
    optimization_flag_matcher = re.compile("^O(\d+)$")
    
    # Regular expression to match diretory flags e.g. -I/usr/include, -L/usr/lib etc.
    # Adapted from example at https://stackoverflow.com/a/33021907/298171
    directory_flag_matcher = re.compile(r"^[IL]((?:[^/]*/)*)(.*)$")
    
    # Ordered list of all possible C++ standard flags --
    # adapted from Clang’s LangStandards.def, https://git.io/vSRX9
    cxx_standard = FlagSet("std=%s", ('c++98', 'gnu++98', 'c++0x', 'gnu++0x', 'c++11', 'gnu++11',
                                      'c++1y', 'gnu++1y', 'c++14', 'gnu++14', 'c++1z', 'gnu++1z',
                                      'c++17', 'gnu++17', 'c++2a', 'gnu++2a'))
    
    @classmethod
    def fake_optimization_flags(cls, flags):
        """ Prune out fake optimization flags e.g. -O8, -O785 etc.
            N.B. Consider renaming this function to `false_flags`, 
            in order to search-engine optimize for the Google searches
            of Breitbart and InfoWars readers (who love that shit).
        """
        match_func = cls.optimization_flag_matcher.match
        opt_set = cls.optimization.set
        return frozenset(
            filter(lambda flag: bool(match_func(flag)) and \
                                    (flag not in opt_set), flags))
    
    @classmethod
    def nonexistent_path_flags(cls, flags):
        """ Filter out include- or lib-path flags pointing to directories
            that do not actually exist, from a set of flags: """
        match_func = cls.directory_flag_matcher.match
        check_func = os.path.exists
        return frozenset(
            filter(lambda flag: bool(match_func(flag)) and \
                                    (not check_func(flag[1:])), flags))
    
    @classmethod
    def highest_optimization_level(cls, flags):
        """ Strip all but the highest optimization-level compiler flag
            from a set of (de-dashed) flags. Returns a new set. """
        # Which flags are optflags?
        optflags = flags.intersection(cls.optimization.set)
        
        # Exit if the `flags` set contained no optflags:
        if len(optflags) < 1:
            return flags - cls.fake_optimization_flags(flags)
        
        # Find the optflag with the highest index into cls.optimization_flags:
        flags_index = reduce(lambda x, y: max(x, y),
                          map(lambda flag: cls.optimization.index(flag),
                              optflags))
        
        # Assemble all non-optflags in a new set:
        out = flags - cls.optimization.set
        out -= cls.fake_optimization_flags(flags)
        
        # Append the highest-indexed optflag we found, and return:
        out |= { cls.optimization[flags_index] }
        return out
    
    @classmethod
    def highest_cxx_standard_level(cls, flags):
        """ Strip all but the highest C++-standard-level compiler flag
            from a set of (de-dashed) flags. Returns a new set. """
        # Which flags are stdflags?
        stdflags = flags.intersection(cls.cxx_standard.set)
        
        # Exit if the `flags` set contained no stdflags:
        if len(stdflags) < 1:
            return flags
        
        # Find the stdflag with the highest index into cls.cxx_standard_flags:
        flags_index = reduce(lambda x, y: max(x, y),
                          map(lambda flag: cls.cxx_standard.index(flag),
                              stdflags))
        
        # Assemble all non-stdflags in a new set:
        out = flags - cls.cxx_standard.set
        
        # Append the highest-indexed stdflag we found, and return:
        out |= { cls.cxx_standard[flags_index] }
        return out
    
    def __new__(cls, *configs):
        """ Create either a new, uninitialized ConfigUnion instance, or -
            in the case where the ConfigUnion was constructed with only
            one config instance - just return that sole existing config:
        """
        length = len(list(configs))
        if length == 0:
            raise AttributeError("ConfigUnion requires 1+ config instances")
        elif length == 1:
            return list(configs)[0]
        return super(ConfigUnion, cls).__new__(cls)
    
    def __init__(self, *configs):
        """ Initialize a ConfigUnion instance with one or more config
            object instances, as needed (although using only one makes
            very little sense, frankly):
        """
        self.configs = []
        for config in configs:
            if hasattr(config, 'configs'):
                # extract configs from a ConfigUnion instance:
                self.configs.extend(config.configs)
            else:
                # append the (non-ConfigUnion) config:
                self.configs.append(config)
    
    def __len__(self):
        """ The length of a ConfigUnion instance is equal to how many sub-configs it has """
        return len(self.configs)
    
    def __getitem__(self, key):
        """ Return a sub-config from the ConfigUnion instance via subscripting """
        return self.configs[key]
    
    def sub_config_types(self):
        """ Return a set of the class names for all sub-configs of this ConfigUnion instance """
        return { config.__class__.__name__ for config in self.configs }
    
    @union_of(name='includes')
    def get_includes(self, includes):
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_includes()`: """
        out = includes - self.nonexistent_path_flags(includes)
        return out
    
    @union_of(name='libs')
    def get_libs(self, libs):
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_libs()`: """
        return libs
    
    @union_of(name='cflags')
    def get_cflags(self, cflags):
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_cflags()`: """
        # Consolidate optimization and C++ standard flags,
        # passing only the respective highest-value flags:
        out = self.highest_cxx_standard_level(
              self.highest_optimization_level(cflags))
        out -= self.nonexistent_path_flags(out)
        return out
    
    @union_of(name='ldflags')
    def get_ldflags(self, ldflags):
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_ldflags()`: """
        out = ldflags - self.nonexistent_path_flags(ldflags)
        return out


def CC(conf, outfile, infile, verbose=DEFAULT_VERBOSITY):
    """ Execute the C compiler, as named in the `CC` environment variable,
        falling back to the compiler specified in Python `sysconfig`: """
    return back_tick("%s %s -c %s -o %s" % (environ_override('CC'),
                                            conf.get_cflags(),
                                            infile, outfile), ret_err=True,
                                                              raise_err=True,
                                                              verbose=verbose)

def CXX(conf, outfile, infile, verbose=DEFAULT_VERBOSITY):
    """ Execute the C++ compiler, as named in the `CXX` environment variable,
        falling back to the compiler specified in Python `sysconfig`: """
    return back_tick("%s %s -c %s -o %s" % (environ_override('CXX'),
                                            conf.get_cflags(),
                                            infile, outfile), ret_err=True,
                                                              raise_err=True,
                                                              verbose=verbose)

def LD(conf, outfile, *infiles, **kwargs):
    """ Execute the dynamic linker, as named in the `LDCXXSHARED` environment variable,
        falling back to the linker specified in Python `sysconfig`: """
    return back_tick("%s %s %s -o %s" % (environ_override('LDCXXSHARED'),
                                         conf.get_ldflags(),
                                         " ".join(infiles), outfile), ret_err=True,
                                                                      raise_err=True,
                                                                      verbose=kwargs.pop('verbose', DEFAULT_VERBOSITY))

def AR(conf, outfile, *infiles, **kwargs):
    """ Execute the library archiver, as named in the `AR` environment variable,
        falling back to the library archiver specified in Python `sysconfig`: """
    # This function is the ugly duckling here because:
    #   a) it does not use the `conf` arg at all, and
    #   b) it has to manually amend 'ARFLAGS' it would seem
    #       b)[1] ... most configuration-getting pc-configgish flag tools
    #                 could not give less fucks about 'ARFLAGS', and so.
    return back_tick("%s %s %s %s" % (environ_override('AR'),
                                      "%ss" % environ_override('ARFLAGS'),
                                      outfile, " ".join(infiles)), ret_err=True,
                                                                   raise_err=True,
                                                                   verbose=kwargs.pop('verbose', DEFAULT_VERBOSITY))

test_generator_source = b"""
#include "Halide.h"
using namespace Halide;

class Brighten : public Halide::Generator<Brighten> {
        
    public:
        enum class Layout { Planar, Interleaved, Either, Specialized };
        
    public:
        Input<Buffer<uint8_t>> input{     "input",    3 };
        GeneratorParam<Layout> layout{    "layout",        Layout::Planar,
                                    {{    "planar",        Layout::Planar },
                                     {    "interleaved",   Layout::Interleaved },
                                     {    "either",        Layout::Either },
                                     {    "specialized",   Layout::Specialized }}};
    
    public:
        Input<uint8_t> offset{            "offset"      };
        Output<Buffer<uint8_t>> brighter{ "brighter", 3 };
        Var x, y, c;
    
    public:
        void generate() {
            // Define the Func.
            brighter(x, y, c) = input(x, y, c) + offset;
            
            // Schedule it.
            brighter.vectorize(x, 16);
            
            if (layout == Layout::Planar) {
            } else if (layout == Layout::Interleaved) {
                input
                    .dim(0).set_stride(3)
                    .dim(2).set_stride(1);
                
                brighter
                    .dim(0).set_stride(3)
                    .dim(2).set_stride(1);
                
                input.dim(2).set_bounds(0, 3);
                brighter.dim(2).set_bounds(0, 3);
                brighter.reorder(c, x, y).unroll(c);
            } else if (layout == Layout::Either) {
                input.dim(0).set_stride(Expr());
                brighter.dim(0).set_stride(Expr());
            } else if (layout == Layout::Specialized) {
                input.dim(0).set_stride(Expr());
                brighter.dim(0).set_stride(Expr());
                
                Expr input_is_planar =
                    (input.dim(0).stride() == 1);
                Expr input_is_interleaved =
                    (input.dim(0).stride() == 3 &&
                     input.dim(2).stride() == 1 &&
                     input.dim(2).extent() == 3);
                
                Expr output_is_planar =
                    (brighter.dim(0).stride() == 1);
                Expr output_is_interleaved =
                    (brighter.dim(0).stride() == 3 &&
                     brighter.dim(2).stride() == 1 &&
                     brighter.dim(2).extent() == 3);
                
                brighter.specialize(input_is_planar && output_is_planar);
                brighter.specialize(input_is_interleaved && output_is_interleaved)
                    .reorder(c, x, y).unroll(c);
            }
        }
};

HALIDE_REGISTER_GENERATOR(Brighten, brighten);
"""

def print_cache():
    from pprint import pprint
    pprint(ConfigBase.base_field_cache, indent=4)

def main():
    from utils import print_config, terminal_width
    from utils import test_compile
    
    brewedHalideConfig = BrewedHalideConfig()
    brewedPythonConfig = BrewedPythonConfig()
    pythonConfig = PythonConfig()
    sysConfig = SysConfig()
    pkgConfig = PkgConfig()
    numpyConfig = NumpyConfig()
    
    configUnionOne = ConfigUnion(sysConfig)
    configUnion = ConfigUnion(brewedHalideConfig, sysConfig)
    configUnionAll = ConfigUnion(brewedHalideConfig, sysConfig,
                                 brewedPythonConfig, pythonConfig,
                                                     pkgConfig,
                                                     numpyConfig)
    
    
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
    print("TESTING: PkgConfig ...")
    print("")
    print_config(pkgConfig)
    
    print("=" * terminal_width)
    print("")
    print("TESTING: NumpyConfig ...")
    print("")
    print_config(numpyConfig)
    
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
    print("TESTING: ConfigUnion<SysConfig> ...")
    print("")
    print_config(configUnionOne)
    
    print("=" * terminal_width)
    print("")
    print("TESTING: ConfigUnion<BrewedHalideConfig, SysConfig> ...")
    print("")
    print_config(configUnion)
    
    print("=" * terminal_width)
    print("")
    print("TESTING: ConfigUnion<BrewedHalideConfig, SysConfig,")
    print("                     BrewedPythonConfig, PythonConfig, PkgConfig, NumpyConfig> ...")
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
    
    """  Reveal the cached field-value dictionary: """
    print("=" * terminal_width)
    print("")
    print("PRINTING: ConfigBase.base_field_cache -- dict<str> ...")
    print("")
    print_cache()
    

def corefoundation_check():
    from utils import print_config, terminal_width
    from utils import test_compile
    try:
        from Foundation import NSBundle
        from CoreFoundation import (CFBundleGetAllBundles,
                                    CFBundleGetValueForInfoDictionaryKey,
                                    CFBundleCopyBundleURL) # CFBundleGetMainBundle
    except ImportError:
        print("CoreFoundation module not found, skipping PyObjC test")
        return
    
    is_python_bundle = lambda bundle: CFBundleGetValueForInfoDictionaryKey(bundle, 'CFBundleIdentifier') == u'org.python.python'
    # python_bundle_set = set(filter(is_python_bundle, CFBundleGetAllBundles())) - { CFBundleGetMainBundle() }
    python_bundle_set = set(filter(is_python_bundle, CFBundleGetAllBundles()))
    python_bundle = python_bundle_set.pop()
    nsbundle = NSBundle.alloc().initWithURL_(CFBundleCopyBundleURL(python_bundle))
    bundlepath = str(nsbundle.bundlePath())
    prefix = os.path.dirname(os.path.dirname(bundlepath))
    
    brewedHalideConfig = BrewedHalideConfig()
    pyConfig = PythonConfig(prefix)
    configUnion = ConfigUnion(brewedHalideConfig, pyConfig)
    
    print("=" * terminal_width)
    print("")
    print("TESTING: ConfigUnion with PythonConfig PyObjC prefix %s ... " % prefix)
    print("                                              bundle path %s ... " % bundlepath)
    print("")
    print_config(configUnion)
    
    print("=" * terminal_width)
    print("")
    print("TEST COMPILATION: CXX(configUnion, <out>, <in>) ...")
    print("")
    test_compile(configUnion, test_generator_source)

if __name__ == '__main__':
    main()
    try:
        import objc
    except ImportError:
        print("SKIPPING: PyObjC-based CoreFoundation test (PyObjC not installed)")
    else:
        objc # SHUT UP, PYFLAKES!
        corefoundation_check()
