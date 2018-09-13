# -*- coding: utf-8 -*-

from __future__ import print_function

import abc
import collections
import os
import re
import six
import sys
import sysconfig
import typing as tx

try:
    from functools import reduce
except ImportError:
    pass

from ctypes.util import find_library
from functools import wraps

import filesystem
import compiledb
from errors import ConfigurationError, ConfigCommandError
from filesystem import which, back_tick, script_path
from filesystem import Directory
from ocd import OCDSet, OCDFrozenSet
from utils import is_string, modulize, stringify, u8bytes, u8str

__all__ = ('SHARED_LIBRARY_SUFFIX', 'STATIC_LIBRARY_SUFFIX',
           'DEFAULT_VERBOSITY',
           'ConfigSubBase',
           'ConfigBaseMeta', 'environ_override',
           'ConfigBase', 'Macro', 'Macros',
           'PythonConfig', 'BrewedPythonConfig',
           'SysConfig', 'PkgConfig', 'NumpyConfig',
                                     'BrewedConfig',
                                     'BrewedHalideConfig',
                                     'BrewedImreadConfig',
           'ConfigUnion',
           'CC', 'CXX', 'LD', 'AR',
           'ts')

__dir__ = lambda: list(__all__)

SHARED_LIBRARY_SUFFIX: str = os.path.splitext(find_library("c"))[-1].lower()
STATIC_LIBRARY_SUFFIX: str = (SHARED_LIBRARY_SUFFIX == ".dll") and ".lib" or ".a"

DEFAULT_VERBOSITY: bool = True

# WTF HAX
TOKEN: str = ' -'

# Possibly a string:
MaybeStr = tx.Optional[str]

# Any kind of set:
TC = tx.TypeVar('TC', covariant=True)
AnySet = tx.Union[tx.Set[TC],
                  tx.FrozenSet[TC],
                  OCDSet,
                  OCDFrozenSet]

# Ancestor type variable annotation:
Ancestor = tx.TypeVar('Ancestor', bound=abc.ABC, covariant=True)

# Type variable for creating homogenously-typed tuple
# typing values factory-stype (q.v. TupleType function sub.):
HomogenousTypeVar = tx.TypeVar('HomogenousTypeVar')
# TupleTypeReturnType = tx.Union[tx.Type[tx.Tuple[HomogenousTypeVar, ...]],
#                                tx.Type[tx.ClassVar[tx.Tuple[HomogenousTypeVar, ...]]]]
TupleTypeReturnType = tx.Type[tx.Tuple[HomogenousTypeVar, ...]]

def TupleType(length: int,
              tuptyp: tx.Type[HomogenousTypeVar] = str,
              clsvar: bool = False) -> TupleTypeReturnType:
    assert length > 0
    out = tx.Tuple[tuple(tuptyp for idx in range(length))]
    return clsvar and tx.ClassVar[out] or out

SubBaseAncestor: tx.Type[Ancestor] = six.with_metaclass(abc.ABCMeta, abc.ABC)
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
        
        (In fact, you may be able to get away with only implementing `cc_flag_string()`,
        `cxx_flag_string()`, and `get_ldflags()` – those are the only methods explicitly
        called by CC/CXX/LD; AR doesn’t even use its config-instance parameter at the
        time of writing.)
        
        You don’t strictly need to inherit from ConfigSubBase – in fact, that is unwise;
        I recommend inheriting from ConfigBase (q.v. class definition sub.) as that will
        get you all of the goodies like FieldList inheritance, the “prefix” property and
        the “subdirectory()” method, and other stuff you can read about below.
    """
    
    base_field_cache: tx.ClassVar[tx.Dict[str, tx.Tuple[str, ...]]] = collections.OrderedDict()
    field_cache:      tx.ClassVar[tx.Dict[str, tx.Tuple[str, ...]]] = collections.OrderedDict()
    
    # Prefix get/set/delete methods:
    
    @property
    @abc.abstractmethod
    def prefix(self) -> Directory: pass
    
    @prefix.setter
    @abc.abstractmethod
    def prefix(self,
               value: filesystem.ts.DirectoryLike): pass
    
    @prefix.deleter
    @abc.abstractmethod
    def prefix(self): pass
    
    # Name get method:
    
    @property
    @abc.abstractmethod
    def name(self) -> str: pass
    
    # The `subdirectory` method is used throughout
    # many Config-ish classes:
    
    @abc.abstractmethod
    def subdirectory(self,
                     subdir: tx.AnyStr,
                     whence: filesystem.ts.MaybeDirectoryLike = None) -> MaybeStr: pass
    
    # These four methods prepare the command strings,
    # using the result(s) from calling one or more
    # of the get_* methods (q.v. prototypes sub.)
    # to compose their arguments:
    
    @abc.abstractmethod
    def cc_flag_string(self) -> str: pass
    
    @abc.abstractmethod
    def cxx_flag_string(self) -> str: pass
    
    @abc.abstractmethod
    def ld_flag_string(self) -> str: pass
    
    @abc.abstractmethod
    def ar_flag_string(self) -> str: pass
    
    # Stringification and representation methods:
    
    @abc.abstractmethod
    def to_string(self,
                  field_list: tx.Optional[tx.Iterable[str]] = None) -> str: pass
    
    @abc.abstractmethod
    def __repr__(self) -> str: pass
    
    @abc.abstractmethod
    def __str__(self) -> str: pass
    
    @abc.abstractmethod
    def __bytes__(self) -> bytes: pass
    
    # These four get_* methods make up the bare-bones
    # requirement for what a Config-ish class needs
    # to provide:
    
    @abc.abstractmethod
    def get_includes(self) -> str: pass
    
    @abc.abstractmethod
    def get_libs(self) -> str: pass
    
    @abc.abstractmethod
    def get_cflags(self) -> str: pass
    
    @abc.abstractmethod
    def get_ldflags(self) -> str: pass


class ConfigBaseMeta(abc.ABCMeta):
    
    """ The metaclass for all Config-ish classes we define here; used with
        ConfigBase (q.v. class definition sub.)
    """
    
    def __new__(metacls, name, bases, attributes, **kwargs) -> type:
        if not 'base_fields' in attributes:
            attributes['base_fields'] = tuple()
        base_fields: OCDSet = OCDSet(attributes['base_fields'])
        for base in bases:
            if hasattr(base, 'base_fields'):
                base_fields |= frozenset(base.base_fields)
            if hasattr(base, 'fields'):
                base_fields |= frozenset(base.fields)
        attributes['base_fields'] = tuple(base_fields)
        ConfigSubBase.base_field_cache[name] = tuple(base_fields)
        cls = super(ConfigBaseMeta, metacls).__new__(metacls, name,
                                                              bases,
                                                              attributes,
                                                            **kwargs)
        ConfigSubBase.register(cls)
        ConfigSubBase.field_cache[name] = getattr(cls, 'fields', tuple())
        return cls

def environ_override(name: str) -> str:
    """ environ_override(name) returns either the environment variable
        named “name” or, failing to find that, the configuration variable
        from the `sysconfig` module named “name.” This allows environment
        variables to seamlessly override `sysconfig` variables.
    """
    return os.environ.get(name,
            sysconfig.get_config_var(name) or '')

BaseAncestor: tx.Type[Ancestor] = six.with_metaclass(ConfigBaseMeta, ConfigSubBase)
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
    
    base_fields: TupleType(5, clsvar=True) = ('prefix', 'get_includes',
                                                        'get_libs',
                                                        'get_cflags',
                                                        'get_ldflags')
    
    dir_fields: TupleType(6, clsvar=True) = ('bin', 'include',
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
        
        __slots__: TupleType(3, clsvar=True) = ('stored_fields',
                                                'exclude_fields',
                                                'include_dir_fields')
        
        def store(self, *fields):
            self.stored_fields: frozenset = frozenset(fields)
            if self.include_dir_fields:
                self.stored_fields |= frozenset(ConfigBase.dir_fields)
        
        def __init__(self, *more_fields, **kwargs):
            self.include_dir_fields: bool = bool(kwargs.pop('dir_fields', False))
            self.exclude_fields: frozenset = frozenset(kwargs.pop('exclude', tuple()))
            self.store(*more_fields)
        
        def __get__(self,
                    instance: tx.Any,
                    cls: tx.Optional[type] = None) -> tx.Tuple[str, ...]:
            if cls is None:
                cls = type(instance)
            out: OCDSet = OCDSet(self.stored_fields)
            if hasattr(cls, 'base_fields'):
                out |= frozenset(cls.base_fields)
            out -= self.exclude_fields
            return tuple(out)
        
        def __set__(self,
                    instance: tx.Any,
                    iterable: tx.Iterable[str]):
            self.store(*iterable)
        
        def __delete__(self,
                       instance: tx.Any):
            raise AttributeError("Can't delete a FieldList attribute")
    
    @property
    def prefix(self) -> Directory:
        """ The path to the Python installation prefix """
        if not hasattr(self, '_prefix'):
            self._prefix: Directory = Directory(sys.prefix)
        return getattr(self, '_prefix')
    
    @prefix.setter
    def prefix(self,
               value: filesystem.ts.DirectoryLike):
        prefixd: Directory = Directory(value)
        if not prefixd.exists:
            raise ValueError(f"prefix path does not exist: {prefixd}")
        self._prefix: Directory = prefixd
    
    @prefix.deleter
    def prefix(self):
        if hasattr(self, '_prefix'):
            del self._prefix
    
    @property
    def name(self) -> str:
        """ The name of the Config instance. This defaults to the name of its class. """
        return type(self).__name__
    
    def subdirectory(self,
                     subdir: tx.AnyStr,
                     whence: filesystem.ts.MaybeDirectoryLike = None) -> MaybeStr:
        """ Return the path to a subdirectory within this Config instances’ prefix """
        return self.prefix.subpath(subdir, whence, requisite=True)
    
    def cc_flag_string(self) -> str:
        """ Get the string template for the C compiler command """
        cflags: str = self.get_cflags()
        return           f"{environ_override('CC')} {cflags} -c %s -o %s"
    
    def cxx_flag_string(self) -> str:
        """ Get the string template for the C++ compiler command """
        cflags: str = self.get_cflags()
        return          f"{environ_override('CXX')} {cflags} -c %s -o %s"
    
    def ld_flag_string(self) -> str:
        """ Get the string template for the dynamic linker command """
        ldflags: str = self.get_ldflags()
        return   f"{environ_override('LDCXXSHARED')} {ldflags} %s -o %s"
    
    def ar_flag_string(self) -> str:
        """ Get the string template for the command executing the archiver
            (née the “static linker”)
        """
        arflags: str = environ_override('ARFLAGS')
        if 's' not in arflags:
            arflags += 's'
        return              f"{environ_override('AR')} {arflags} %s %s"
    
    def to_string(self,
                  field_list: tx.Optional[tx.Iterable[str]] = None) -> str:
        """ Stringify the instance, using either a provided list of fields to evaluate,
            or if none was provided, the iterable-of-strings class variable “fields”.
        """
        if not field_list:
            field_list: tx.Iterable[str] = type(self).fields
        return stringify(self, field_list)
    
    def __repr__(self) -> str:
        return stringify(self, type(self).fields)
    
    def __str__(self) -> str:
        return stringify(self, type(self).fields)
    
    def __bytes__(self) -> bytes:
        return u8bytes(repr(self))

ConfigType = tx.TypeVar('ConfigType', bound=ConfigBase, covariant=True)

class SetWrap(ConfigBase):
    
    fields = ConfigBase.FieldList('sub_config_type', 'includes_set',
                                                     'libs_set',
                                                     'cflags_set',
                                                     'ldflags_set', exclude=['prefix'],
                                                                    dir_fields=False)
    def __init__(self, config: ConfigType):
        if not isinstance(config, (ConfigBase, ConfigSubBase)):
            raise TypeError("OCDSetWrap.__init__(…) requires a ConfigBase or ConfigSubBase argument")
        self.config: ConfigType = config
        self.prefix = config.prefix
    
    def sub_config_type(self) -> str:
        return self.config.name
    
    @property
    def name(self) -> str:
        """ The name of the Config instance. In this case, it is the typename
            of the config class, followed by the name property of the wrapped
            config instance (which defaults to the name of its class).
        """
        typename: str = type(self).__name__
        wrappedname: str = self.sub_config_type()
        return f"{typename}<{wrappedname}>"
    
    def get_includes(self) -> str:
        return self.config.get_includes()
    
    def get_libs(self) -> str:
        return self.config.get_libs()
    
    def get_cflags(self) -> str:
        return self.config.get_cflags()
    
    def get_ldflags(self) -> str:
        return self.config.get_ldflags()
    
    def includes_set(self) -> set:
        includes: str = self.get_includes()
        return { flag.strip() for flag in f" {includes}".split(TOKEN) if len(flag.strip()) }
    
    def libs_set(self) -> set:
        libs: str = self.get_libs()
        return { flag.strip() for flag in f" {libs}".split(TOKEN) if len(flag.strip()) }
    
    def cflags_set(self) -> set:
        cflags: str = self.get_cflags()
        return { flag.strip() for flag in f" {cflags}".split(TOKEN) if len(flag.strip()) }
    
    def ldflags_set(self) -> set:
        ldflags: str = self.get_ldflags()
        return { flag.strip() for flag in f" {ldflags}".split(TOKEN) if len(flag.strip()) }


class Macro(object):
    
    __slots__: TupleType(3, clsvar=True) = ('name', 'definition', 'undefine')
    
    STRING_ZERO: str = '0'
    STRING_ONE: str  = '1'
    
    @staticmethod
    def is_string_value(putative: tx.Any, value: int = 0) -> bool:
        """ Predicate function for checking for the values of stringified integers """
        # N.B. `is_string(…)` is a lambda imported from halogen.utils:
        if not is_string(putative):
            return False
        intdef: int = 0
        try:
            intdef += int(putative, base=10)
        except ValueError:
            return False
        return intdef == int(value)
    
    def __init__(self, name: str, definition: MaybeStr = None,
                                  undefine: bool = False):
        """ Initialize a new Macro instance, specifiying a name, a definition (optionally),
            and a boolean flag (optionally) indicating that the macro is “undefined” --
            that is to say, that it is a so-called “undef macro”.
        """
        if not name:
            raise ConfigurationError("Macro() requires a valid name")
        string_zero: bool = self.is_string_value(definition)
        string_one: bool = self.is_string_value(definition, value=1)
        string_something: bool = string_zero or string_one
        self.name: str = name
        self.definition: MaybeStr = (not string_something or None) and definition
        self.undefine: bool = string_zero or undefine
    
    def to_string(self) -> str:
        """ Stringify the macro instance as a GCC- or Clang-compatible command-line switch,
            e.g. “DMACRO_NAME=Some_Macro_Value” -- or just “DMACRO_NAME” or “UMACRO_NAME”,
            if applicable.
        """
        if self.undefine:
            return f"U{u8str(self.name)}"
        if self.definition is not None:
            return f"D{u8str(self.name)}={u8str(self.definition)}"
        return f"D{u8str(self.name)}"
    
    def to_tuple(self) -> tx.Tuple[str, str]:
        """ Tuple-ize the macro instance -- return a tuple in the form (name, value)
            as per the macro’s contents. The returned tuple always has a value field;
            in the case of undefined macros, the value is '0' -- stringified zero --
            and in the case of macros lacking definition values, the value is '1' --
            stringified one.
        """
        if self.undefine:
            return (u8str(self.name),
                          self.STRING_ZERO)
        if self.definition is not None:
            return (u8str(self.name),
                    u8str(self.definition))
        return (u8str(self.name),
                      self.STRING_ONE)
    
    def __repr__(self) -> str:
        return stringify(self, type(self).__slots__)
    
    def __str__(self) -> str:
        return self.to_string()
    
    def __bytes__(self) -> bytes:
        return u8bytes(self.to_string())
    
    def __bool__(self) -> bool:
        """ An instance of Macro is considered Falsey if undefined, Truthy if not. """
        return not self.undefine


class Macros(dict):
    
    def define(self, name: str, definition: MaybeStr = None,
                                undefine: bool = False) -> Macro:
        return self.add(Macro(name,
                              definition,
                              undefine=undefine))
    
    def undefine(self, name: str, **kwargs) -> Macro:
        return self.add(Macro(name, undefine=True))
    
    def add(self, macro: Macro) -> Macro:
        name: str = macro.name
        if bool(macro):
            # macro is defined:
            self[name] = macro.definition or Macro.STRING_ONE
        else:
            # macro is an undef macro:
            self[name] = Macro.STRING_ZERO
        return macro
    
    def delete(self, name: str, **kwargs) -> bool:
        if name in self:
            del self[name]
            return True
        return False
    
    def definition_for(self, name: str) -> Macro:
        if name not in self:
            return Macro(name, undefine=True)
        return Macro(name, self[name])
    
    def to_tuple(self) -> tx.Tuple[Macro, ...]:
        out: tx.List[Macro] = []
        for k, v in self.items():
            out.append(Macro(k, v).to_tuple())
        return tuple(out)
    
    def to_string(self) -> str:
        stringified: str = TOKEN.join(Macro(k, v).to_string() \
                                        for k, v in self.items()).strip()
        return f"{TOKEN.lstrip()}{stringified}"
    
    def __str__(self) -> str:
        return self.to_string()
    
    def __bytes__(self) -> bytes:
        return u8bytes(self.to_string())

FRAMEWORK_RE_STR: str = r"""(^.*)(?:^|/)(\w+).framework(?:/(?:Versions/([^/]+)/)?\2)?$"""
FRAMEWORK_RE: tx.Optional[re.Pattern] = None

def infoForFramework(filename: str) -> tx.Optional[tx.List[str]]:
    """ Originally from PyObjC: http://bit.ly/2MPVbuz
        … returns (location, name, version) or None
    """
    global FRAMEWORK_RE
    if FRAMEWORK_RE is None:
        import re
        FRAMEWORK_RE = re.compile(FRAMEWORK_RE_STR)
    is_framework: tx.List[str] = FRAMEWORK_RE.findall(filename)
    if not is_framework:
        return None
    return is_framework[-1]

class PythonConfig(ConfigBase):
    
    """ A config class that provides its values via the output of the command-line
        `python-config` tool (associated with the running Python interpreter).
    """
    
    # 'Frameworks', 'Headers', 'Resources', 'framework'
    
    fields = ConfigBase.FieldList('pyconfig', 'pyconfigpath',
                                  'library_name', 'library_file', 'header_file',
                                  'framework_name',
                                  'framework_path',
                                  # 'Frameworks',
                                  # 'Headers', 'Resources',
                                   dir_fields=False)
    
    # Name of the `python-config` binary (nearly always just `python-config`):
    pyconfig: str = "python-config"
    pyconfigpath: str = which(pyconfig)
    
    # String of python major-minor version e.g. "2.7", "3.7" etc.
    python_version: str = f"{sys.version_info.major}{os.extsep}{sys.version_info.minor}"
    
    # The semver-ish name of this Python installation:
    library_name: str = f"python{python_version}{sys.abiflags}"
    
    # The actual filename for this Python installations’ shared library:
    library_file: str = f"lib{library_name}{SHARED_LIBRARY_SUFFIX}"
    
    # The actual filename for this Python installations’ base header:
    header_file: str = 'Python.h'
    
    # The name of the framework for this python installation:
    framework_name: str = 'Python.framework'
    
    # the path to the 'Frameworks' directory (empty before calls):
    framework_path: MaybeStr = None
    
    def __init__(self, prefix: filesystem.ts.MaybeDirectoryLike = None):
        """ Initialize PythonConfig, optionally specifying a system prefix """
        if not prefix:
            prefix = Directory(sys.prefix)
        self.prefix = prefix
    
    def bin(self) -> MaybeStr:
        return self.subdirectory("bin")
    
    def include(self) -> MaybeStr:
        return self.subdirectory("include")
    
    def lib(self) -> MaybeStr:
        return self.subdirectory("lib")
    
    def libexec(self) -> MaybeStr:
        return self.subdirectory("libexec") or self.lib()
    
    def libexecbin(self) -> MaybeStr:
        return self.subdirectory('bin', whence=self.subdirectory("libexec"))
    
    def share(self) -> MaybeStr:
        return self.subdirectory("share")
    
    @property
    def framework(self) -> MaybeStr:
        if not self.framework_path:
            # from prefix, search depth-first up (linear):
            if self.framework_name in self.prefix.name:
                head: str = self.prefix.name
                tail: str = "yo dogg" # something not false-y
                while tail:
                    # head, tail = self.prefix.split()
                    head, tail = os.path.split(self.prefix.name)
                    if tail == self.framework_name:
                        # self.framework_path = Directory(head)
                        self.framework_path = head
                        return self.framework_path
            # from prefix, search depth-first down (likely exponential):
            for path, dirs, files in self.prefix.walk(followlinks=True):
                if self.framework_name in dirs:
                    # self.framework_path = Directory(path)
                    self.framework_path = path
                    return self.framework_path
            # give up, using a sensible default:
            # self.framework_path = Directory(self.subdirectory('Frameworks'))
            self.framework_path = self.subdirectory('Frameworks')
        return self.framework_path
    
    def Frameworks(self) -> str:
        return self.framework
    
    def Headers(self) -> str:
        return os.path.join(self.framework,
                            self.framework_name, 'Versions',
                            self.python_version, 'Headers')

    def Resources(self) -> str:
        return os.path.join(self.framework,
                            self.framework_name, 'Versions',
                            self.python_version, 'Resources')
    
    def get_includes(self) -> str:
        return back_tick(f"{self.pyconfigpath} --includes")
    
    def get_libs(self) -> str:
        return back_tick(f"{self.pyconfigpath} --libs")
    
    def get_cflags(self) -> str:
        return back_tick(f"{self.pyconfigpath} --cflags")
    
    def get_ldflags(self) -> str:
        return back_tick(f"{self.pyconfigpath} --ldflags")


class BrewedPythonConfig(PythonConfig):
    
    """ A config class that provides its values through calls to the Mac Homebrew
        command-line `brew` tool (with fallback calls to the PythonConfig class).
    """
    
    fields = ConfigBase.FieldList('brew',
                                  'brew_name', dir_fields=True)
    
    # Path to the Homebrew executable CLT `brew`
    brew: MaybeStr = which("brew")
    
    def __init__(self, brew_name: MaybeStr = None):
        """ Initialize BrewedPythonConfig, optionally naming a homebrew formula """
        if not self.brew:
            raise ConfigCommandError("Can't find Homebrew “brew” executable")
        if not brew_name:
            brew_name = 'python'
        self.brew_name: str = brew_name
        prefix: str = back_tick(f"{self.brew} --prefix {self.brew_name}", ret_err=False)
        super(BrewedPythonConfig, self).__init__(prefix=prefix)
    
    def include(self) -> MaybeStr:
        for path, dirs, files in self.prefix.walk(followlinks=True):
            if self.header_file in files:
                return path
        return super(BrewedPythonConfig, self).include()
    
    def lib(self) -> MaybeStr:
        for path, dirs, files in self.prefix.walk(followlinks=True):
            if self.library_file in files:
                return path
        return super(BrewedPythonConfig, self).lib()


class SysConfig(PythonConfig):
    
    fields = ConfigBase.FieldList('Frameworks', 'Headers',
                                                'Resources',
                                                'with_openssl', dir_fields=True)
    
    """ A config class that provides its values using the Python `sysconfig` module,
        with fallback calls to PythonConfig, and environment variable overrides
        for all `sysconfig` variables in use; the option to include the `sysconfig`
        OpenSSL compile and link flags is available via the “with_openssl” boolean
        parameter to the constructor.
    """
    
    def __init__(self, with_openssl: bool = False):
        """ Initialize SysConfig, passing the `data` path as the prefix up the chain
            of inheritance. Specify the optional “with_openssl” parameter as True
            to obtain a SysConfig instance that will include the OpenSSL compile and
            link flags in its output.
        """
        self.with_openssl: bool = with_openssl
        super(SysConfig, self).__init__(prefix=sysconfig.get_path("data"))
    
    def bin(self) -> MaybeStr:
        return sysconfig.get_path("scripts")
    
    def include(self) -> MaybeStr:
        return sysconfig.get_path("include")
    
    def lib(self) -> MaybeStr:
        return environ_override('LIBDIR')
    
    def Frameworks(self) -> str:
        return environ_override('PYTHONFRAMEWORKPREFIX')
    
    def Headers(self) -> str:
        return os.path.join(environ_override('PYTHONFRAMEWORKPREFIX'),
                            self.framework_name, 'Versions',
                            self.python_version, 'Headers')
    
    def Resources(self) -> str:
        return os.path.join(environ_override('PYTHONFRAMEWORKPREFIX'),
                            self.framework_name, 'Versions',
                            self.python_version, 'Resources')
    
    def get_includes(self) -> str:
        out: str = f"-I{sysconfig.get_path('include')}"
        if sysconfig.get_path("include") != \
           sysconfig.get_path("platinclude"):
            out += f" -I{sysconfig.get_path('platinclude')}"
            out = out.strip()
        if self.with_openssl:
            out += f" {environ_override('OPENSSL_INCLUDES')}"
        return out.strip()
    
    def get_libs(self) -> str:
        out: str = f"-l{self.library_name} {environ_override('LIBS')} {environ_override('SYSLIBS')}"
        if not environ_override('PYTHONFRAMEWORK'):
            out += f" {environ_override('LINKFORSHARED')}".strip()
        if self.with_openssl:
            out += f" {environ_override('OPENSSL_LIBS')}".strip()
        return out.strip()
    
    def get_cflags(self) -> str:
        out: str = f"-I{sysconfig.get_path('include')} {environ_override('CFLAGS')} {environ_override('CXXFLAGS')}".strip()
        if sysconfig.get_path("include") != \
           sysconfig.get_path("platinclude"):
            out = f"-I{sysconfig.get_path('platinclude')} {out.strip()}".strip()
        if self.with_openssl:
            out += f" {environ_override('OPENSSL_INCLUDES')}"
        return out.strip()
    
    def get_ldflags(self) -> str:
        ldstring: str = ""
        libpths: TupleType(3) = (environ_override('LIBDIR'),
                                 environ_override('LIBPL'),
                                 environ_override('LIBDEST'))
        for pth in libpths:
            if os.path.exists(pth):
                ldstring += f"{TOKEN}L{pth}"
        if self.with_openssl:
            ldstring += f" {environ_override('OPENSSL_LDFLAGS')}"
        out: str = f"{ldstring.strip()} -l{self.library_name} {environ_override('LIBS')} {environ_override('SYSLIBS')}"
        if not environ_override('PYTHONFRAMEWORK'):
            out += f" {environ_override('LINKFORSHARED')}"
        if self.with_openssl:
            out += f" {environ_override('OPENSSL_LIBS')}"
        return out.strip()


class PkgConfig(ConfigBase):
    
    """ A config class that provides its values using the `pkg-config`
        command-line tool, for a package name recognized by same.
    """
    
    fields = ConfigBase.FieldList('cflags',
                                  'pkgconfig',
                                  'pkg_name', dir_fields=True)
    
    # List of cflags to use with all pkg-config-based classes:
    cflags: tx.ClassVar[OCDFrozenSet] = OCDFrozenSet(("funroll-loops",
                                                      "mtune=native",
                                                      "O3"))
    
    # Location of the `pkg-config` binary:
    pkgconfig: str = which('pkg-config')
    
    # Cache of complete package list:
    packages: tx.ClassVar[OCDSet] = OCDSet()
    did_load_packages: tx.ClassVar[bool] = False
    
    @classmethod
    def load_packages(cls) -> int:
        """ Load all package names from `pkg-config` """
        if not cls.did_load_packages:
            from errors import ExecutionError
            script: str = which('all-pkgconfig-packages.sh', pathvar=script_path())
            try:
                cls.packages |= OCDFrozenSet(back_tick(script).split('\n'))
            except ExecutionError:
                cls.did_load_packages = False
            else:
                cls.did_load_packages = True
        return len(cls.packages)
    
    @classmethod
    def add_package(cls, pkg_name: str):
        """ Add a package name to the set of all package names """
        cls.packages |= { pkg_name }
    
    @classmethod
    def check_package(cls, pkg_name: str) -> bool:
        """ Check a package name for validity against the loaded set of names """
        return pkg_name in cls.packages
    
    def __init__(self, pkg_name: MaybeStr = None):
        """ Initialize PkgConfig, optionally naming a package (the default is “python3”) """
        if not pkg_name:
            pkg_name = 'python3'
        self.pkg_name: str = pkg_name
        self.add_package(pkg_name)
        self.prefix = back_tick(f"{self.pkgconfig} {self.pkg_name} --variable=prefix", ret_err=False)
    
    def bin(self) -> MaybeStr:
        return self.subdirectory("bin")
    
    def include(self) -> MaybeStr:
        return self.subdirectory("include")
    
    def lib(self) -> MaybeStr:
        return self.subdirectory("lib")
    
    def libexec(self) -> MaybeStr:
        return self.subdirectory("libexec") or self.lib()
    
    def libexecbin(self) -> MaybeStr:
        return self.subdirectory('bin', whence=self.subdirectory('libexec'))
    
    def share(self) -> MaybeStr:
        return self.subdirectory("share")
    
    @property
    def name(self) -> str:
        """ The name of the Config instance. In this case, it is the name of the class,
            along with the value of the “pkg_name” instance variable, specifying the name
            of the `pkg-config` package with whose data the instance was initialized.
        """
        return f"{type(self).__name__}(pkg_name=“{self.pkg_name}”)"
    
    def get_includes(self) -> str:
        return back_tick(f"{self.pkgconfig} {self.pkg_name} --cflags-only-I",
                         ret_err=False)
    
    def get_libs(self) -> str:
        return back_tick(f"{self.pkgconfig} {self.pkg_name} --libs-only-l --libs-only-other --static",
                         ret_err=False)
    
    def get_cflags(self) -> str:
        pc_cflags = back_tick(f"{self.pkgconfig} {self.pkg_name} --cflags",
                              ret_err=False)
        return f"{TOKEN}{TOKEN.join(self.cflags)} {pc_cflags}".strip()
    
    def get_ldflags(self) -> str:
        return back_tick(f"{self.pkgconfig} {self.pkg_name} --libs --static",
                         ret_err=False)


class NumpyConfig(ConfigBase):
    
    subpackages: TupleType(2, clsvar=True) = ('npymath', 'mlib')
    
    fields = ConfigBase.FieldList('subpackages',
                                  'get_numpy_include_directory',
                                  'info', 'macros',
                                  'include', 'lib', dir_fields=False)
    
    @classmethod
    def get_numpy_include_directory(cls) -> Directory:
        if not hasattr(cls, 'include_path'):
            import numpy
            cls.include_path: Directory = Directory(pth=numpy.get_include())
        return cls.include_path
    
    def __init__(self):
        """ Prefix is likely /…/numpy/core """
        from shlex import quote
        self.info: tx.DefaultDict[str, OCDSet] = collections.defaultdict(OCDSet)
        self.macros: Macros = Macros()
        self.prefix: Directory = self.get_numpy_include_directory().parent()
        import numpy.distutils, numpy.version
        for package in self.subpackages:
            infodict: tx.Dict[str, tx.Tuple[str, ...]] = numpy.distutils.misc_util.get_info(package)
            for k, v in infodict.items():
                self.info[k] |= frozenset(v)
        self.info['include_dirs'] |= { os.fspath(self.get_numpy_include_directory()) }
        for macro_tuple in self.info['define_macros']:
            self.macros.define(*macro_tuple)
        self.macros.define('NUMPY')
        self.macros.define('NUMPY_VERSION',            f'\\"{quote(numpy.version.version)}\\"')
        self.macros.define('NPY_NO_DEPRECATED_API',     'NPY_1_7_API_VERSION')
        self.macros.define('PY_ARRAY_UNIQUE_SYMBOL',    'YO_DOGG_I_HEARD_YOU_LIKE_UNIQUE_SYMBOLS')
    
    def include(self) -> MaybeStr:
        return self.subdirectory("include")
    
    def lib(self) -> MaybeStr:
        return self.subdirectory("lib")
    
    def get_includes(self) -> str:
        return " ".join(f"-I{include_dir}" for include_dir \
                                 in self.info['include_dirs'])
    
    def get_libs(self) -> str:
        return " ".join(f"-l{library}" for library \
                             in self.info['libraries'])
    
    def get_cflags(self) -> str:
        macros: str = self.macros.to_string()
        includes: str = self.get_includes()
        extra_compile_args: str = " ".join(self.info['extra_compile_args'])
        return f"{macros} {includes} {extra_compile_args}".strip()
    
    def get_ldflags(self) -> str:
        linkdirs: str = " ".join(f"-L{library_dir}" for library_dir \
                                          in self.info['library_dirs'])
        libs: str = self.get_libs()
        extra_link_args: str = " ".join(self.info['extra_link_args'])
        return f"{linkdirs} {libs} {extra_link_args}".strip()


class BrewedConfig(ConfigBase):
    
    """ A config class that provides its values through calls to the Mac Homebrew
        command-line `brew` tool, for arbitrary named Homebrew formulae.
    """
    
    fields = ConfigBase.FieldList('brew',
                                  'brew_name',
                                  'cflags', dir_fields=False)
    
    # Name of, and prefix for, the Homebrew installation:
    brew: str = which('brew')
    
    # List of cflags to use with all Homebrew-based config classes:
    cflags: tx.ClassVar[OCDFrozenSet] = OCDFrozenSet(("funroll-loops",
                                                      "mtune=native",
                                                      "O3"))
    
    def __init__(self, brew_name=None):
        """ Initialize BrewedConfig, optionally naming a formula (the default is “halide”) """
        if not brew_name:
            brew_name = 'halide'
        self.brew_name: str = brew_name
        self.prefix: filesystem.ts.DirectoryLike = back_tick(f"{self.brew} --prefix {self.brew_name}",
                                                               ret_err=False)
    
    def bin(self) -> MaybeStr:
        return self.subdirectory("bin")
    
    def include(self) -> MaybeStr:
        return self.subdirectory("include")
    
    def lib(self) -> MaybeStr:
        return self.subdirectory("lib")
    
    def libexec(self) -> MaybeStr:
        return self.subdirectory("libexec") or self.lib()
    
    def libexecbin(self) -> MaybeStr:
        return self.subdirectory('bin', whence=self.subdirectory('libexec'))
    
    def share(self) -> MaybeStr:
        return self.subdirectory("share")
    
    @property
    def name(self) -> str:
        """ The name of the Config instance. In this case, it is the name of the class,
            along with the value of the “brew_name” instance variable, specifying the
            name of the Homebrew formula with whose data the instance was initialized.
        """
        return f"{type(self).__name__}(brew_name=“{self.brew_name}”)"
    
    def get_includes(self) -> str:
        return f"-I{self.include()}"
    
    def get_libs(self) -> str:
        return ""
    
    def get_cflags(self) -> str:
        return f"{TOKEN}{TOKEN.join(self.cflags)} {self.get_includes()}".strip()
    
    def get_ldflags(self) -> str:
        return f"-L{self.lib()}"


class BrewedHalideConfig(BrewedConfig):
    
    """ A config class that provides its values through calls to the Mac Homebrew
        command-line `brew` tool, specifically pertaining to the Halide formula.
    """
    
    fields = ConfigBase.FieldList('library', dir_fields=True)
    
    # Name of the Halide library (sans “lib” prefix and file extension):
    library: str = "Halide"
    
    # List of Halide-specific cflags to use:
    cflags: tx.ClassVar[OCDFrozenSet] = OCDFrozenSet(("std=c++1z",
                                                      "stdlib=libc++")) | BrewedConfig.cflags
    
    def __init__(self):
        """ Initialize BrewedHalideConfig (constructor takes no arguments) """
        super(BrewedHalideConfig, self).__init__(brew_name=self.library.lower())
    
    @property
    def name(self) -> str:
        """ The name of the Config instance. This defaults to the name of its class. """
        return type(self).__name__
    
    def get_libs(self) -> str:
        return f"-l{self.library}"
    
    def get_ldflags(self) -> str:
        return f"-L{self.lib()} -l{self.library}"


class BrewedImreadConfig(BrewedConfig):
    
    """ A config class that provides its values through calls to the Mac Homebrew
        command-line `brew` tool, specifically pertaining to the “libimread” formula.
    """
    
    fields = ConfigBase.FieldList('library',
                                  'imread_config', dir_fields=True)
    
    # Name of the libimread library (sans “lib” prefix and file extension)
    # and the name of the corresponding Homebrew formula:
    library: str = "imread"
    brew_name: str = 'libimread'
    
    # Name of, and path to, the `imread-config` utility:
    imread_config: str = which('imread-config')
    
    def __init__(self):
        """ Complete override of BrewedConfig’s __init__ method: """
        self.prefix: filesystem.ts.DirectoryLike = back_tick(f"{self.imread_config} --prefix", ret_err=False)
    
    @property
    def name(self) -> str:
        """ The name of the Config instance. This defaults to the name of its class. """
        return type(self).__name__
    
    def get_includes(self) -> str:
        return back_tick(f"{self.imread_config} --includes", ret_err=False)
    
    def get_libs(self) -> str:
        return back_tick(f"{self.imread_config} --libs", ret_err=False)
    
    def get_cflags(self) -> str:
        return back_tick(f"{self.imread_config} --cflags", ret_err=False)
    
    def get_ldflags(self) -> str:
        return back_tick(f"{self.imread_config} --ldflags", ret_err=False)


class ConfigUnion(ConfigBase, tx.Collection[ConfigType]):
    
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
            used with function stubs, e.g. like so:
            
            class ConfigUnion(ConfigBase):
            
                @union_of('libs')                   # function name without "get_" prefix;
                def get_libs(self, libs):           # function definition, naming an input set;
                    return libs & self.otherstuff   # transform the input set, if necessary,
                                                    # and return it
        """
        
        __slots__: TupleType(1, clsvar=True) = ('name',)
        
        def __init__(self, name: str):
            """ Initialize the @union_of decorator, stashing the name of the function
                to call upon those config-class instances wrapped by the ConfigUnion
                instance in question. """
            self.name: str = f"get_{str(name)}"
        
        def __call__(self, base_function):
            """ Process the decorated method, passed in as `base_function` --
                The `base_function` call should process the populated input set of flags
                and return a set (either a modified version of the input set, or not). """
            # N.B. the curly-brace expression below is a set comprehension:
            @wraps(base_function)
            def getter(this):
                out: OCDSet = OCDSet()
                for config in this.configs:
                    function_to_call = getattr(config, self.name)
                    out |= { flag.strip() for flag in f" {function_to_call()}".split(TOKEN) }
                return (TOKEN.join(sorted(base_function(this, out)))).strip()
            return getter
    
    class FlagSet(tx.Collection[str]):
        
        """ A sugary-sweet class for stowing a set of flags whose order is significant. """
        
        joiner: tx.ClassVar[str] = f",{TOKEN}"
        __slots__: TupleType(2, clsvar=True) = ('flags', 'set')
        
        def __init__(self, template: str, flaglist: tx.Iterable[str]):
            self.flags: tx.List[str] = [template % flag for flag in flaglist]
            self.set: tx.FrozenSet[str] = frozenset(self.flags)
        
        def __contains__(self, key: str) -> bool:
            return key in self.set
        
        def __bool__(self) -> bool:
            return True
        
        def __iter__(self) -> tx.Iterable[str]:
            return iter(self.flags)
        
        def __len__(self) -> int:
            return len(self.flags)
        
        def __getitem__(self, key) -> str:
            return self.flags[key]
        
        def index(self, value: str) -> int:
            return self.flags.index(value)
        
        def __repr__(self) -> str:
            return f"[{TOKEN}{self.joiner.join(self.flags)} ]"
        
        def __str__(self) -> str:
            return f"[{TOKEN}{self.joiner.join(self.flags)} ]"
        
        def __bytes__(self) -> bytes:
            return u8bytes(repr(self))
    
    # Ordered list of all possible optimization flags:
    optimization: tx.ClassVar[FlagSet] = FlagSet("O%s", ('0', 's', 'fast', '1',
                                                         'g', '',  '2',    '3',
                                                         '4')) # 4 is technically a fake
    
    # Regular expression to match fake optimization flags e.g. -O8, -O785 etc.
    optimization_flag_matcher = re.compile("^O(\d+)$").match
    
    # Regular expression to match diretory flags e.g. -I/usr/include, -L/usr/lib etc.
    # Adapted from example at https://stackoverflow.com/a/33021907/298171
    directory_flag_matcher = re.compile(r"^[IL]((?:[^/]*/)*)(.*)$").match
    
    # Ordered list of all possible C++ standard flags --
    # adapted from Clang’s LangStandards.def, https://git.io/vSRX9
    cxx_standard: tx.ClassVar[FlagSet] = FlagSet("std=%s", ('c++98', 'gnu++98',
                                                            'c++0x', 'gnu++0x',
                                                            'c++11', 'gnu++11',
                                                            'c++1y', 'gnu++1y',
                                                            'c++14', 'gnu++14',
                                                            'c++1z', 'gnu++1z',
                                                            'c++17', 'gnu++17',
                                                            'c++2a', 'gnu++2a'))
    
    @classmethod
    def fake_optimization_flags(cls, flags: AnySet) -> OCDFrozenSet:
        """ Prune out fake optimization flags e.g. -O8, -O785 etc.
            N.B. Consider renaming this function to `false_flags`, 
            in order to search-engine optimize for the Google searches
            of Breitbart and InfoWars readers (who love that shit).
        """
        match_func = cls.optimization_flag_matcher
        opt_set: tx.FrozenSet[str] = cls.optimization.set
        return OCDFrozenSet(
            filter(lambda flag: bool(match_func(flag)) and \
                                    (flag not in opt_set), flags))
    
    @classmethod
    def nonexistent_path_flags(cls, flags: AnySet) -> OCDFrozenSet:
        """ Filter out include- or lib-path flags pointing to directories
            that do not actually exist, from a set of flags: """
        match_func = cls.directory_flag_matcher
        check_func = os.path.exists
        return OCDFrozenSet(
            filter(lambda flag: bool(match_func(flag)) and \
                                    (not check_func(flag[1:])), flags))
    
    @classmethod
    def highest_optimization_level(cls, flags: AnySet) -> AnySet:
        """ Strip all but the highest optimization-level compiler flag
            from a set of (de-dashed) flags. Returns a new set. """
        # Which flags are optflags?
        optflags: AnySet = flags.intersection(cls.optimization.set)
        
        # Exit if the `flags` set contained no optflags:
        if len(optflags) < 1:
            return flags - cls.fake_optimization_flags(flags)
        
        # Find the optflag with the highest index into cls.optimization.flags:
        flags_index: int = reduce(lambda x, y: max(x, y),
                              map(lambda flag: cls.optimization.index(flag),
                                  optflags))
        
        # Assemble all non-optflags in a new set:
        out: AnySet = flags - cls.optimization.set
        out -= cls.fake_optimization_flags(flags)
        
        # Append the highest-indexed optflag we found, and return:
        out |= { cls.optimization[flags_index] }
        return out
    
    @classmethod
    def highest_cxx_standard_level(cls, flags: AnySet) -> AnySet:
        """ Strip all but the highest C++-standard-level compiler flag
            from a set of (de-dashed) flags. Returns a new set. """
        # Which flags are stdflags?
        stdflags: AnySet = flags.intersection(cls.cxx_standard.set)
        
        # Exit if the `flags` set contained no stdflags:
        if len(stdflags) < 1:
            return flags
        
        # Find the stdflag with the highest index into cls.cxx_standard.flags:
        flags_index: int = reduce(lambda x, y: max(x, y),
                              map(lambda flag: cls.cxx_standard.index(flag),
                                  stdflags))
        
        # Assemble all non-stdflags in a new set:
        out: AnySet = flags - cls.cxx_standard.set
        
        # Append the highest-indexed stdflag we found, and return:
        out |= { cls.cxx_standard[flags_index] }
        return out
    
    def __new__(cls, *configs) -> ConfigType:
        """ Create either a new, uninitialized ConfigUnion instance, or -
            in the case where the ConfigUnion was constructed with only
            one config instance - just return that sole existing config:
        """
        length: int = len(list(configs))
        if length == 0:
            raise AttributeError("ConfigUnion requires 1+ config instances")
        elif length == 1:
            return list(configs)[0]
        instance: ConfigUnion = super(ConfigUnion, cls).__new__(cls)
        instance.configs: tx.List[ConfigType] = []
        return instance
    
    def __init__(self, *configs):
        """ Initialize a ConfigUnion instance with one or more config
            object instances, as needed (although using only one makes
            very little sense, frankly):
        """
        if hasattr(self, 'configs'):
            for config in configs:
                if hasattr(config, 'configs'):
                    # extract configs from a ConfigUnion instance:
                    self.configs.extend(config.configs)
                else:
                    # append the (non-ConfigUnion) config:
                    self.configs.append(config)
    
    def __len__(self) -> int:
        """ The length of a ConfigUnion instance is equal to the number of its sub-configs """
        return len(self.configs)
    
    def __iter__(self) -> tx.Iterable[ConfigType]:
        return iter(self.configs)
    
    def __getitem__(self, key: int) -> ConfigType:
        """ Access one of the ConfigUnion instances’ sub-configs via subscript """
        return self.configs[key]
    
    def sub_config_types(self) -> OCDFrozenSet:
        """ Retrieve a set of the names of this ConfigUnion instances’ sub-configs """
        return OCDFrozenSet( config.name for config in self.configs )
    
    def __contains__(self, key: tx.Union[tx.AnyStr, ConfigType]) -> bool:
        """ Determine if a config type is contained within this ConfigUnion instance """
        return getattr(key, 'name', key) in self.sub_config_types()
    
    @property
    def name(self) -> str:
        """ The name of the Config instance. In this case, it is the class name, followed
            by a bracketed list of the types (in C++ template-type-parameter style) of all
            of this ConfigUnion instances’ sub-config instances -- or rather, it is a
            bracketed list of the *names* of those sub-config instances (e.g. the
            `instance.name` property) which is often, but not always only, that instances’
            class name. Like, q.v. config-class name property definitions supra., dogg.
            
            Internally, this property calls ConfigUnion.sub_config_types(self) to furnish
            itself with the sub-config type list.
        """
        typelist: str = ", ".join(self.sub_config_types())
        return f"{type(self).__name__}<{typelist}>"
    
    @union_of(name='includes')
    def get_includes(self, includes) -> set:
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_includes()`: """
        out = includes - self.nonexistent_path_flags(includes)
        return out
    
    @union_of(name='libs')
    def get_libs(self, libs) -> set:
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_libs()`: """
        return libs
    
    @union_of(name='cflags')
    def get_cflags(self, cflags) -> set:
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_cflags()`: """
        # Consolidate optimization and C++ standard flags,
        # passing only the respective highest-value flags:
        out = self.highest_cxx_standard_level(
              self.highest_optimization_level(cflags))
        out -= self.nonexistent_path_flags(out)
        return out
    
    @union_of(name='ldflags')
    def get_ldflags(self, ldflags) -> set:
        """ Return the union of all flags amassed from the calling
            of all base Config objects' `get_ldflags()`: """
        out = ldflags - self.nonexistent_path_flags(ldflags)
        return out


def CC(conf: ConfigType, outfile: str, infile: str, **kwargs) -> tx.Tuple[str, ...]:
    """ Execute the C compiler, as named in the `CC` environment variable,
        falling back to the compiler specified in Python `sysconfig`:
    """
    cdb: tx.Optional[compiledb.CDBSubBase] = kwargs.pop('cdb', None)
    command: str = conf.cc_flag_string() % (infile, outfile)
    if isinstance(cdb, compiledb.CDBSubBase):
        cdb.push(infile, command, directory=kwargs.pop('directory', None),
                                  destination=outfile)
    return back_tick(command,
                     ret_err=True,
                     verbose=kwargs.pop('verbose', DEFAULT_VERBOSITY))

def CXX(conf: ConfigType, outfile: str, infile: str, **kwargs) -> tx.Tuple[str, ...]:
    """ Execute the C++ compiler, as named in the `CXX` environment variable,
        falling back to the compiler specified in Python `sysconfig`:
    """
    cdb: tx.Optional[compiledb.CDBSubBase] = kwargs.pop('cdb', None)
    command: str = conf.cxx_flag_string() % (infile, outfile)
    if isinstance(cdb, compiledb.CDBSubBase):
        cdb.push(infile, command, directory=kwargs.pop('directory', None),
                                  destination=outfile)
    return back_tick(command,
                     ret_err=True,
                     verbose=kwargs.pop('verbose', DEFAULT_VERBOSITY))

def LD(conf: ConfigType, outfile: str, *infiles, **kwargs) -> tx.Tuple[str, ...]:
    """ Execute the dynamic linker, as named in the `LDCXXSHARED` environment variable,
        falling back to the linker specified in Python `sysconfig`:
    """
    command: str = conf.ld_flag_string() % (" ".join(infiles), outfile)
    return back_tick(command,
                     ret_err=True,
                     verbose=kwargs.pop('verbose', DEFAULT_VERBOSITY))

def AR(conf: ConfigType, outfile: str, *infiles, **kwargs) -> tx.Tuple[str, ...]:
    """ Execute the library archiver, as named in the `AR` environment variable,
        falling back to the library archiver specified in Python `sysconfig`:
    """
    # This function is the ugly duckling here because:
    #   a) it does not use the `conf` arg at all, and
    #   b) it has to manually amend 'ARFLAGS' it would seem
    #       b)[1] ... most configuration-getting pc-configgish flag tools
    #                 could not give less fucks about 'ARFLAGS', and so.
    command: str = conf.ar_flag_string() % (outfile, " ".join(infiles))
    return back_tick(command,
                     ret_err=True,
                     verbose=kwargs.pop('verbose', DEFAULT_VERBOSITY))


modulize({
               'MaybeStr' : MaybeStr,
                 'AnySet' : AnySet,
               'Ancestor' : Ancestor,
      'HomogenousTypeVar' : HomogenousTypeVar,
              'TupleType' : TupleType,
             'ConfigType' : ConfigType
}, 'config.ts', "Typenames local to the config module", __file__)

import config.ts as ts

del find_library
del TC
# del MaybeStr
# del AnySet
del Ancestor
del HomogenousTypeVar
# del ConfigType
del SubBaseAncestor
del BaseAncestor

def test():
    from utils import print_config
    from utils import test_compile
    from utils import print_cache
    import test_generators
    
    brewedHalideConfig: ts.ConfigType = BrewedHalideConfig()
    brewedPythonConfig: ts.ConfigType = BrewedPythonConfig()
    pythonConfig: ts.ConfigType = PythonConfig()
    sysConfig: ts.ConfigType = SysConfig()
    pkgConfig: ts.ConfigType = PkgConfig()
    numpyConfig: ts.ConfigType = NumpyConfig()
    
    sysConfigSetWrap: SetWrap = SetWrap(sysConfig)
    numpyConfigSetWrap: SetWrap = SetWrap(numpyConfig)
    
    configUnionOne: ts.ConfigType = ConfigUnion(SysConfig(with_openssl=True))
    configUnion: ts.ConfigType = ConfigUnion(brewedHalideConfig, sysConfig)
    configUnionAll: ts.ConfigType = ConfigUnion(brewedHalideConfig, sysConfig,
                                             brewedPythonConfig, pythonConfig,
                                                                 pkgConfig,
                                                                 numpyConfig)
    
    configUnionSetWrap: SetWrap = SetWrap(configUnion)
    
    """ 1. Test basic config methods: """
    
    print_config(brewedHalideConfig)
    print_config(sysConfig)
    print_config(sysConfigSetWrap)
    print_config(pkgConfig)
    print_config(numpyConfig)
    print_config(numpyConfigSetWrap)
    print_config(brewedPythonConfig)
    print_config(pythonConfig)
    print_config(configUnionOne)
    print_config(configUnion)
    print_config(configUnionSetWrap)
    print_config(configUnionAll)
    
    """ 2. Test compilation with different configs: """
    
    test_compile(brewedHalideConfig, test_generators.brighten_source)
    test_compile(configUnionSetWrap, test_generators.brighten_source)
    test_compile(configUnionAll,     test_generators.brighten_source)
    
    test_compile(brewedHalideConfig, test_generators.autoscheduler_source)
    test_compile(configUnionSetWrap, test_generators.autoscheduler_source)
    test_compile(configUnionAll,     test_generators.autoscheduler_source)
    
    """ 3. Reveal the cached field-value dictionary: """
    
    print_cache(ConfigBase, 'base_field_cache')
    print_cache(ConfigBase, 'field_cache')
    
    # Check “ts” submodule:
    assert ts
    assert ts.MaybeStr
    assert ts.AnySet
    assert ts.Ancestor
    assert ts.ConfigType


def corefoundation_check():
    try:
        from Foundation import NSBundle
        from CoreFoundation import (CFBundleGetAllBundles,
                                    CFBundleGetValueForInfoDictionaryKey,
                                    CFBundleCopyBundleURL) # CFBundleGetMainBundle
    except ImportError:
        print("CoreFoundation module not found, skipping PyObjC test")
        return
    
    from utils import print_config
    from utils import test_compile
    import test_generators
    
    FUNC_NAME_WTF = CFBundleGetValueForInfoDictionaryKey
    bundle_id: str = 'org.python.python'
    is_python_bundle: bool = lambda bundle: FUNC_NAME_WTF(bundle, 'CFBundleIdentifier') == bundle_id
    python_bundle_set: tx.Set[str] = set(filter(is_python_bundle, CFBundleGetAllBundles()))
    # python_bundle_set -= { CFBundleGetMainBundle() }
    python_bundle = python_bundle_set.pop()
    nsbundle = NSBundle.alloc().initWithURL_(CFBundleCopyBundleURL(python_bundle))
    bundlepath: Directory = Directory(nsbundle.bundlePath())
    # prefix = os.path.dirname(os.path.dirname(bundlepath))
    prefix: Directory = bundlepath.parent().parent()
    
    brewedHalideConfig: ts.ConfigType = BrewedHalideConfig()
    pyConfig: ts.ConfigType = PythonConfig(prefix)
    configUnion: ts.ConfigType = ConfigUnion(brewedHalideConfig, pyConfig)
    
    """ 5. Dump the ConfigUnion instance used in the CoreFoundation test: """
    
    print_config(configUnion)
    
    """ 6. Test compilation with the one-off CoreFoundation-specific ConfigUnion: """
    
    test_compile(configUnion, test_generators.brighten_source)
    test_compile(configUnion, test_generators.autoscheduler_source)

if __name__ == '__main__':
    test()
    try:
        import objc
    except ImportError:
        print("SKIPPING: PyObjC-based CoreFoundation test (PyObjC not installed)")
    else:
        objc # SHUT UP, PYFLAKES!
        corefoundation_check()
