#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import abc
import collections
import inspect
import six
import sys
import types
import typing as tx
import typing_extensions as tX

from functools import wraps
from multidict import MultiDict                              # type: ignore
from multidict._abc import _TypingMeta as TypingMeta         # type: ignore
from multidict._abc import MultiMapping, MutableMultiMapping # type: ignore

__all__ = ('UTF8_ENCODING',
           'tuplize', 'listify',
           'Originator', 
           'GenericAlias', 'KeyValue', 'Namespace', 'DictNamespace',
                                                    'SimpleNamespace',
                                                    'MultiNamespace',
                                                    'TypeAndBases', 'TypeSpace',
                                                    'ty',
           'find_generic_for_type',
           'TerminalSize', 'terminal_size', 'terminal_width',
                                            'terminal_height',
           'wrap_value', 'Memoizer', 'memoize',
           'current_umask', 'masked_permissions',
           'modulize',
           'append_paths', 'remove_paths',
           'string_types', 'is_string', 'stringify',
                                        'u8bytes',
                                        'u8str',
           'suffix_searcher',
           'terminal_print', 'print_cache',
                             'print_config',
                             'test_compile')

__dir__ = lambda: list(__all__)

abstract = None # SHUT UP, PYFLAKES!!
PRINT_ORIGIN_TYPES = True
PRINT_GENERIC_INFO = True
UTF8_ENCODING = 'UTF-8'

S = tx.TypeVar('S', bound=str, covariant=True)
T = tx.TypeVar('T', covariant=True)
U = tx.TypeVar('U', covariant=True)
ContraT = tx.TypeVar('ContraT', contravariant=True)

def tuplize(*items) -> tx.Tuple[tx.Any, ...]:
    return tuple(item for item in items if item is not None)

def listify(*items) -> tx.List[tx.Any]:
    return list(item for item in items if item is not None)

class GenericAlias(tX._GenericAlias, _root=True):
    __slots__: tx.Tuple[str, ...] = tuplize('__origin__', '__args__')
    
    def __repr__(self) -> str:
        """ Bespoke re-implementation of typing._GenericAlias.__repr__ """
        type_repr: tx.Callable[[tx.Any], str] = Originator.type_repr
        name: str = ''
        args: str = ''
        modulename: str = ''
        origin: tx.Type[tx.Any] = self.__origin__
        if (self._name != 'Callable' or                               # type: ignore
                len(self.__args__) == 2 and self.__args__[0] is ...): # type: ignore
            if self._name:                                            # type: ignore
                if not hasattr(origin, '__module__'):
                    module: tx.Optional[types.ModuleType] = inspect.getmodule(origin)
                    if module:
                        modulename += module.__name__
                    else:
                        modulename += "utils"
                else:
                    modulename += origin.__module__
                if len(modulename) > 0:
                    modulename += "."
                name += f"{modulename}{self._name}" # type: ignore
            else:
                name += type_repr(origin) # type: ignore
            if not getattr(self, '_special', False):
                args += f'[{", ".join([type_repr(a) for a in self.__args__])}]' # type: ignore
            return f'{name}{args}'
        if getattr(self, '_special', False):
            return 'typing.Callable'
        return (f'typing.Callable' # type: ignore
                f'[[{", ".join([type_repr(a) for a in self.__args__[:-1]])}], '
                f'{type_repr(self.__args__[-1])}]')
    
    def copy_with(self, params: tx.Iterable[tx.TypeVar]) -> "GenericAlias":
        return type(self)(self.__origin__,         # type: ignore
                          params, name=self._name, # type: ignore
                                  inst=self._inst) # type: ignore
    
    @classmethod
    def alias(cls, origin, name: tx.Optional[str] = None,
                         params: tx.Iterable[tx.TypeVar] = tuple(),
                           inst: bool = True) -> "GenericAlias":
        """ Public implementation of the typing._alias() helper function """
        out = cls(origin,
                  params, special=True,
                          inst=inst,
                          name=name or origin.__name__)
        return out

class Originator(TypingMeta):
    
    @staticmethod
    def type_repr(obj: tx.Any) -> str:
        """ Adapted from `_type_repr(…)`, an internal helper function
            from the “typing” module:
        """
        if isinstance(obj, type):
            if obj.__module__ == 'builtins':
                return obj.__qualname__
            if not hasattr(obj, '__module__'):
                module: tx.Optional[types.ModuleType] = inspect.getmodule(obj)
                modulename: str = module.__name__
            else:
                modulename: str = obj.__module__
            if modulename:
                return f'{modulename}.{obj.__qualname__}'
            return f'{obj.__module__}.{obj.__qualname__}'
        if obj is ...:
            return '...'
        if isinstance(obj, types.FunctionType):
            return obj.__name__
        return repr(obj)
    
    def __repr__(cls) -> str:
        return cls.type_repr(cls)
    
    def __getitem__(cls,
                 params: tx.Union[tx.TypeVar,
                                  tx.Iterable[tx.TypeVar]]) -> GenericAlias:
        if not hasattr(params, '__iter__') or params.__class__ is type:
            params: tx.Tuple[tx.TypeVar, ...] = tuplize(params)
        else:
            params: tx.Tuple[tx.TypeVar, ...] = tuplize(*params)
        origin: tx.Type[tx.Any] = getattr(cls, '__origin__')
        generic_getitem = hasattr(origin, '__class_getitem__') and \
                          getattr(origin, '__class_getitem__') or \
                          getattr(origin, '__getitem__')
        unwrapped = getattr(generic_getitem, '__wrapped__',
                            generic_getitem)
        signature: inspect.Signature = inspect.signature(unwrapped)
        argcount: int = len(signature.parameters)
        if argcount == 2 and hasattr(cls, '__parameters__'):
            if len(params) > 0:
                cls.__parameters__ = params
            out = unwrapped(cls, params)
        else:
            out = unwrapped(params)
        return GenericAlias(out.__origin__,
                            out.__parameters__, name=getattr(out, '_name', origin.__name__),
                                                inst=getattr(out, '_inst', True))
    
    @classmethod
    def __prepare__(metacls,
                       name: str,
                      bases: tx.Iterable[type],
                   **kwargs) -> tx.MutableMapping[str, tx.Any]:
        """ Maintain declaration order in class members, and
            import @abstractmethod from the `abc` module into
            the class namespace as @abstract:
        """
        return collections.OrderedDict(abstract=abc.abstractmethod)
    
    def __new__(metacls,
                   name: str,
                  bases: tx.Iterable[type],
             attributes: tx.MutableMapping[str, tx.Any],
               **kwargs) -> type:
        
        """ Metaclass that sets the __origin__ class attribute to the value of
            the un-subscripted base class value
        """
        
        if not '__origin__' in attributes:
            
            # find the first generic base:
            genericbase: tx.Optional[type] = None
            for basecls in bases:
                if hasattr(basecls, '__parameters__'):
                    genericbase = basecls
                    break
                if hasattr(basecls, '__origin__'):
                    genericbase = basecls.__origin__
                    break
                if basecls is tx.Generic:
                    genericbase = basecls
                    break
            
            # Raise if no generics are happened upon:
            if genericbase is None:
                raise TypeError("couldn't find a generic base class")
            
            # Jam it in:
            attributes.update({
                '__originator__' : metacls,
                    '__origin__' : genericbase
            })
        
        # Do the beard:
        cls = super().__new__(metacls, name,  # type: ignore
                                       bases,
                                       dict(attributes),
                                     **kwargs)
        
        # Return to zero:
        return cls

MultiMap: GenericAlias = GenericAlias.alias(MultiMapping,
                                           'MultiMap',
                                            params=(S, T))

MutableMultiMap: GenericAlias = GenericAlias.alias(MutableMultiMapping,
                                                  'MutableMultiMap',
                                                   params=(S, T))

class KeyValue(tx.Generic[T, U]):
    __slots__: tx.Tuple[str, ...] = tuple()
    
    @classmethod
    def __repr__(cls) -> str:
        return Originator.type_repr(cls)
    
    @classmethod
    def __init_subclass__(cls, *args, **kwargs):
        """ Set the __origin__ class value to the primary base class """
        
        super().__init_subclass__() # NO ARGS!
        cls.__origin__ = cls.__base__
        
        if __name__ == '__main__' and PRINT_GENERIC_INFO:
            from pprint import pformat
            print(f"Subclass Name: {cls.__qualname__}")
            print(f"Parameters({len(cls.__parameters__)}): " \
                        f"{listify(*cls.__parameters__)}")
            if hasattr(cls, '__args__'):
                print(f" Arguments({len(cls.__args__)}): " \
                            f"{listify(*cls.__args__)}")
            print(f"Orig Bases({len(cls.__orig_bases__)}): \n" \
                  f"{pformat(listify(*cls.__orig_bases__), indent=4)}")
            print()

class Namespace(KeyValue[T, U], metaclass=Originator):
    __slots__: tx.Tuple[str, ...] = tuple()
    
    @abstract
    def __bool__(self) -> bool: ...
    
    @abstract
    def __len__(self) -> int: ...
    
    @abstract
    def __contains__(self, key: T) -> bool: ...
    
    @abstract
    def __iter__(self) -> tx.Iterator[U]: ...
    
    @abstract
    def get(self, key: T,
        default_value: tx.Optional[U] = None) -> tx.Optional[U]: ...
    
    @abstract
    def __repr__(self) -> str: ...


class DictNamespace(Namespace[T, U], tx.MutableMapping[T, U],
                                     tx.Sized,
                                     tx.Iterable[U],
                                     tx.Container[U]):
    __slots__: tx.Tuple[str, ...] = tuplize('__dict__')
    
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    
    def __bool__(self) -> bool:
        return bool(self.__dict__)
    
    def __len__(self) -> int:
        return len(self.__dict__)
    
    def __contains__(self, key: T) -> bool:
        return key in self.__dict__
    
    def __getitem__(self, key: T) -> U:
        return self.__dict__[key]
    
    def __setitem__(self, key: T, val: U):
        self.__dict__[key] = val
    
    def __delitem__(self, key: T):
        del self.__dict__[key]
    
    def get(self, key: T,
        default_value: tx.Optional[U] = None) -> tx.Optional[U]:
        return self.__dict__.get(key, default_value)
    
    def __iter__(self) -> tx.Iterator[U]:
        return iter(self.__dict__)
    
    def __copy__(self):
        return type(self)(**self.__dict__)
    
    def __repr__(self) -> str:
        keys: tx.List[U] = sorted(self.__dict__, key=lambda k: str(k))
        items: tx.Generator[T, ContraT, str] = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(type(self).__name__, ", ".join(items)) # type: ignore

class SimpleNamespace(DictNamespace[str, T]):
    __slots__: tx.Tuple[str, ...] = tuple()

class MultiNamespace(Namespace[str, T], MultiMap[str, T],
                                        tx.MutableMapping[str, T],
                                        tx.Collection[T]):
    __slots__: tx.Tuple[str, ...] = tuplize('_dict',
                                            '_initialized')
    
    def __init__(self, **kwargs):
        self._dict: MutableMultiMap[str, T] = MultiDict()
        self._dict.update(kwargs)
        self._initialized: bool = True
    
    def initialized(self) -> bool:
        try:
            return super().__getattribute__('_initialized')
        except:
            return False
    
    def mdict(self) -> MutableMultiMap[str, T]:
        return super().__getattribute__('_dict')
    
    def __bool__(self) -> bool:
        return bool(self.mdict())
    
    def __len__(self) -> int:
        return len(self.mdict())
    
    def __contains__(self, key: str) -> bool:
        return key in self.mdict()
    
    def __getitem__(self, key: str) -> T:
        return self.mdict()[key]
    
    def __setitem__(self, key: str, val: T):
        self.mdict()[key] = val
    
    def __delitem__(self, key: str):
        del self.mdict()[key]
    
    def __iter__(self) -> tx.Iterator[T]:
        return iter(dict(self.mdict()))
    
    def __getattr__(self, key: str) -> T:
        return self.getone(key)
    
    def __setattr__(self, key: str, val: T):
        if self.initialized():
            self.mdict().add(key, val)
        else:
            super().__setattr__(key, val)
    
    def add(self, key: str, val: T):
        self.mdict().add(key, val)
    
    def getone(self, key: str) -> T:
        return self.mdict().getone(key)
    
    def getall(self, key: str) -> tx.Tuple[T, ...]:
        return self.mdict().getall(key)
    
    def get(self, key: str,
        default_value: tx.Optional[T] = None) -> tx.Optional[T]:
        return (key in self.mdict()) and self.getone(key) or default_value
    
    def count(self, key: str) -> int:
        return (key in self.mdict()) and len(self.getall(key)) or 0
    
    def zero(self, key: str) -> bool:
        if key in self.mdict():
            del self.mdict()[key]
            return True
        return False
    
    def __copy__(self):
        out = type(self)()
        out.mdict().update(self.mdict())
        return out
    
    def __repr__(self) -> str:
        return repr(self.mdict())

ConcreteType = tx.TypeVar('ConcreteType', bound=type, covariant=True)
CT = tx.TypeVar('CT', bound=type, covariant=True)
BaseType = tx.TypeVar('BaseType', covariant=True)
BT = tx.TypeVar('BT', bound=type, covariant=True)
NewTypeCallable = tx.Callable[[BaseType], BaseType]

class NamedTupleMeta(tx.NamedTupleMeta):
    def __new__(metacls,
                   name: str,
                  bases: tx.Iterable[type],
             attributes: tx.MutableMapping[str, tx.Any],
               **kwargs) -> tx.Type[ConcreteType]:
        out: tx.Type[ConcreteType] = super().__new__(metacls, name, # type: ignore
                                                              bases,
                                                              attributes,
                                                            **kwargs)
        out.__origin__: tx.Type[BaseType] = bases[0].__base__
        return out

class NamedTuple(tx.NamedTuple, metaclass=NamedTupleMeta):
    _root: tx.ClassVar[bool] = True

class TypeAndBases(NamedTuple):
    """ A typed NamedTuple subclass for storing a type plus a list
        of the stringified names of all of its bases:
    """
    Type:   tx.Type[ConcreteType]
    Name:   str = ''
    Bases:  tx.List[str] = []
    
    @classmethod
    def for_type(cls,
              newcls: tx.Type[ConcreteType]) -> "TypeAndBases":
        basenames: tx.List[str] = []
        for base in newcls.__bases__:
            name: str = getattr(base, '__qualname__',
                        getattr(base, '__name__'))
            mod: str = getattr(base, '__module__', '')
            if len(mod) > 1:
                mod += '.'
            basenames.append(f"{mod}{name}")
        return cls(newcls,  # type: ignore
                   newcls.__qualname__,
                   basenames)

class TypeSpace(MultiNamespace[CT]):
    __slots__: tx.Tuple[str, ...] = tuplize('for_origin')
    
    def __init__(self, **kwargs):
        self.for_origin: DictNamespace[CT, BT] = DictNamespace()
        super().__init__(**kwargs)
    
    def add_original(self, cls: tx.Any) -> bool:
        origin: tx.Optional[CT] = getattr(cls, '__origin__', None)
        if not origin:
            return False
        self.for_origin[cls] = origin
        self.add(cls.__name__, origin)
        return True
    
    def add_generic(self, cls: tx.Any) -> bool:
        origin: tx.Optional[CT] = getattr(cls, '__origin__', None)
        if not origin:
            return False
        self.for_origin[origin] = cls
        self.add(origin.__name__, cls)
        return True
    
    def add_generics_from_module(self, module: types.ModuleType) -> int:
        generic_count: int = 0
        for key in dir(module):
            modattr = getattr(module, key)
            if self.add_generic(modattr):
                generic_count += 1
        return generic_count
    
    def NewType(self, name: str, basetype: tx.Type[BT]) -> NewTypeCallable:
        func: NewTypeCallable = tx.NewType(name, basetype)
        func.__origin__ = basetype
        basename: str = basetype.__name__
        self.for_origin[basetype] = func
        self.add(basename, func)
        return func

ty: TypeSpace[ConcreteType] = TypeSpace()

# build a “for_origin” dict in the “ty” namespace:
ty.add_generics_from_module(tx)

ty.add_generic(MultiMap)
ty.add_generic(MutableMultiMap)

ty.add_original(KeyValue)
ty.add_original(Namespace)
ty.add_original(DictNamespace)
ty.add_original(SimpleNamespace)
ty.add_original(MultiNamespace)
ty.add_original(TypeAndBases)
ty.add_original(TypeSpace)

def find_generic_for_type(cls: tx.Type[ConcreteType],
                          missing: tx.Optional[
                                   tx.Type[ConcreteType]] = None) -> tx.Optional[type]:
    if not hasattr(cls, '__mro__'):
        return missing
    for t in cls.__mro__:
        if t in ty.for_origin:
            return ty.for_origin.get(t)
    return missing


class TerminalSize(object):
    
    class Size(tx.NamedTuple):
        
        height: int = 25
        width: int = 120
        
        @property
        def area(self) -> int:
            """ Compute total area """
            return self.width * self.height
        
        @property
        def perimeter(self) -> int:
            """ Calculate perimeter of the size’s bounding box """
            return (self.width * 2) + \
                   (self.height * 2)
        
        @property
        def lines(self) -> int:
            """ known also as how high, the height, the tallness … """
            return self.height
        
        @property
        def columns(self) -> int:
            """ a.k.a how long, width, the x-dimension etc """
            return self.width
        
        def copy(self) -> tx.NamedTuple:
            """ Duplicate the Size instance """
            return self._replace(
                 **self._asdict())
    
    Descriptor = ty.NewType('Descriptor', int)
    
    DEFAULT_LINES:   int = 25
    DEFAULT_COLUMNS: int = 130
    MINIMUM_LINES:   int = 25
    MINIMUM_COLUMNS: int = 25
    
    cache: tx.List[Size] = []
    
    @classmethod
    def ioctl_GWINSZ(cls, descriptor: Descriptor) -> tx.Optional[Size]:
        """ Extract the GWINSZ terminal I/O property value data
            from a file descriptor, using an `ioctl(…)` call to
            obtain the packed Posix data structure, a call to the
           `struct.unpack(…)` module to process the raw ioctl output
            into Python integers
        """
        
        import fcntl, termios, struct
        try:
            cr: tx.Tuple[int, int] = struct.unpack('hh',
                                       fcntl.ioctl(
                                           tx.cast(int, descriptor),
                                                   termios.TIOCGWINSZ,
                                                  '1234')) # type: ignore
        except:
            return None
        
        return cls.Size(*cr) # type: ignore
    
    def __init__(self, DEFAULT_LINES:   tx.Optional[int] = None,
                       DEFAULT_COLUMNS: tx.Optional[int] = None):
        
        """ Initialize the TerminalSize babysitter class """
        
        if DEFAULT_LINES is not None:
            if self.DEFAULT_LINES   !=   DEFAULT_LINES and \
               self.MINIMUM_LINES   <=   DEFAULT_LINES:
               self.DEFAULT_LINES   =    DEFAULT_LINES
        
        if DEFAULT_COLUMNS is not None:
            if self.DEFAULT_COLUMNS != DEFAULT_COLUMNS and \
               self.MINIMUM_COLUMNS <= DEFAULT_COLUMNS:
               self.DEFAULT_COLUMNS =  DEFAULT_COLUMNS
        
        self.store_terminal_size()
        
    def fetch_terminal_size_values(self) -> Size:
        import os
        env = os.environ
        
        # Adapted from this: http://stackoverflow.com/a/566752/298171
        # … first, attempt to pluck out the CGWINSZ terminal values using
        # the stdin/stdout/stderr file descriptor numbers:
        sz: tx.Optional[self.Size] = self.ioctl_GWINSZ(0) or \
                                     self.ioctl_GWINSZ(1) or \
                                     self.ioctl_GWINSZ(2)
        
        # … if that did not work, get the /dev entry name of the terminal
        # in which our process is ensconced, open a descriptor on it for reaing,
        # and use that descriptor to once again attempt to read CGWINSZ values 
        # for the terminal:
        descriptor: self.Descriptor = 0
        if not sz:
            try:
                descriptor = os.open(os.ctermid(),
                                     os.O_RDONLY)
                sz = self.ioctl_GWINSZ(descriptor)
            except:
                pass
            finally:
                if descriptor:
                    os.close(descriptor)
        
        # … if we were unsuccessfull in reading from all three of the standard
        # I/O descriptors •and• a bespoke descriptor opened directly on the
        # /dev entry, make a last-ditch effort to send back values culled from
        # the environment, with truly last-resort possibilities filled in with
        # hardcoded defaults.
        if not sz:
            sz = self.Size(env.get('LINES',   self.DEFAULT_LINES),
                           env.get('COLUMNS', self.DEFAULT_COLUMNS))
        
        # Return plain tuple:
        return sz
    
    def store_terminal_size(self) -> Size:
        size: self.Size = self.fetch_terminal_size_values()
        self.cache.append(size)
        return size
    
    def __call__(self, *args, **kwargs) -> Size:
        if len(self.cache) < 1:
            self.store_terminal_size()
        return self.cache[-1]

terminal_size: TerminalSize = TerminalSize()
terminal_width:  int        = terminal_size().width 
terminal_height: int        = terminal_size().height

if __name__ == '__main__' and PRINT_ORIGIN_TYPES:
    from pprint import pprint
    
    print("=" * terminal_width)
    print('Typing Index: ' \
         f'{len(ty)} types, ' \
         f'{len(ty.mdict())} in ty.mdict, ' \
         f'{len(ty.for_origin)} in ty.for_origin')
    
    print()
    print(ty)
    print()
    
    TOTAL = 30
    lines = []
    
    for k, v in ty.mdict().items():
        strk = f"{k}"
        pads = TOTAL - len(strk)
        padding = pads * " "
        lines.append(f"{padding}{strk} : {v}")
    
    for line in reversed(lines):
        print(line)
    
    print()
    pprint(ty.for_origin)
    print()
    
    print("-" * terminal_width)
    print()

StringType = tx.TypeVar('StringType', bound=type, covariant=True)
PredicateType = tx.Callable[[tx.Any], bool]

string_types: tx.Tuple[tx.Type[StringType], ...] = tuplize(type(''),
                                                           type(b''),
                                                           type(f''),
                                                           type(r''),
                                                          *six.string_types)

is_string: PredicateType = lambda thing: isinstance(thing, string_types)

WrapArg = tx.TypeVar('WrapArg', covariant=True)

def wrap_value(value: tx.Any) -> tx.Callable[[tx.Optional[tx.Iterable[tx.Any]],
                                              tx.Optional[tx.Mapping[tx.Any,
                                                                     tx.Any]]],
                                             tx.Any]:
    return lambda *args, **kwargs: value

none_function = wrap_value(None)

class Memoizer(dict):
    
    """ Very simple memoizer (only works with positional args) """
    
    def __init__(self, function):
        super(Memoizer, self).__init__()
        self.original = function
    
    def __missing__(self, key):
        function = self.original
        self[key] = out = function(*key)
        return out
    
    @property
    def original(self):
        return self.original_function
    
    @original.setter
    def original(self, value):
        if value is None:
            value = none_function
        if callable(value):
            self.original_function = value
        else:
            self.original_function = wrap_value(value)
    
    def __call__(self, function=None):
        if function is None:
            function = self.original
        else:
            self.original = function
        @wraps(function)
        def memoized(*args):
            return self[tuplize(*args)]
        memoized.__original__ = function
        memoized.__instance__ = self
        return memoized

def memoize(function):
    memoinstance = Memoizer(function)
    @wraps(function)
    def memoized(*args):
        return memoinstance[tuplize(*args)]
    memoized.__original__ = function
    memoized.__instance__ = memoinstance
    return memoized

@memoize
def current_umask() -> int:
    import os
    mask = os.umask(0)
    os.umask(mask)
    return mask

def masked_permissions(perms=0o666) -> int:
    return perms & ~current_umask()

def modulize(namespace: tx.MutableMapping[str, tx.Any],
             modulename: str,
             moduledocs: tx.Optional[str] = None,
             modulefile: tx.Optional[str] = None) -> types.ModuleType:
    
    """ Convert a dictionary mapping into a legit Python module """
    
    import os, re
    
    # Update the namespace with '__all__' and '__dir__':
    if '__all__' not in namespace:
        ns_all = tuplize(*sorted(namespace.keys()))
        namespace.update({
            '__all__' : ns_all,
            '__dir__' : lambda: list(ns_all)
        })
    
    # Create a new module with a trivially namespaced name:
    if modulefile:
        relpath: str = os.path.relpath(modulefile,
                 start=os.path.dirname(__file__))
        dotpath: str = re.sub(re.compile(rf"({os.path.sep})"), os.path.extsep, relpath)
        if dotpath.endswith('.py'):
            dotpath = dotpath[:len(dotpath)-3]
        namespacedname: str = f'__dynamic_modules__.halogen.{dotpath}.{modulename}'
        namespace.update({ '__file__' : modulefile })
    else:
        namespacedname: str = f'__dynamic_modules__.halogen.{modulename}'
    namespace.update({ '__package__' : namespacedname })
    
    module: types.ModuleType = types.ModuleType(namespacedname, moduledocs)
    module.__dict__.update(namespace)
    
    # Add to sys.modules, as per import machinery:
    sys.modules.update({ modulename : module })
    
    # Return the new module instance:
    return module

def append_paths(*putatives) -> tx.Dict[str, bool]:
    """ Mutate `sys.path` by appending one or more new paths -- all of which
        are checked for both nonexistence and presence within the existing
        `sys.path` list via inode lookup, and which those failing such checks
        are summarily excluded.
    """
    import os
    out: tx.Dict[str, bool] = {}
    if len(putatives) < 1:
        return out
    paths: tx.FrozenSet[str] = frozenset(sys.path)
    append_paths.oldsyspath: tx.Tuple[str, ...] = tuple(sys.path)
    for pth in putatives:
        if hasattr(pth, 'name'):
            pth = pth.name
        if not os.path.exists(pth):
            out[pth] = False
            continue
        # if pth in paths:
        #     out[pth] = False
        #     continue
        for p in paths:
            if os.path.samefile(p, pth):
                out[pth] = False
                continue
        sys.path.append(pth)
        out[pth] = True
        continue
    return out

append_paths.oldsyspath: tx.Tuple[str, ...] = tuple()

def remove_paths(*putatives) -> tx.Dict[str, bool]:
    """ Mutate `sys.path` by removing one or more existing paths --
        all of which are checked for presence within the existing `sys.path`
        list via inode lookup before being marked for removal, which that
        (the removal) is done atomically.
    """
    import os
    out: tx.Dict[str, bool] = {}
    if len(putatives) < 1:
        return out
    removals: tx.Set[str] = set()
    paths: tx.Set[str] = set(sys.path)
    for pth in putatives:
        if hasattr(pth, 'name'):
            pth = pth.name
        for p in paths:
            if os.path.samefile(p, pth):
                out[pth] = True
                removals |= { p }
                continue
        out[pth] = False
        continue
    paths -= removals
    remove_paths.oldsyspath: tx.Tuple[str, ...] = tuple(sys.path)
    sys.path = list(paths)
    return out

remove_paths.oldsyspath: tx.Tuple[str, ...] = tuple()

def u8encode(source: tx.Any) -> bytes:
    """ Encode a source as bytes using the UTF-8 codec """
    return bytes(source, encoding=UTF8_ENCODING)

def u8bytes(source: tx.Any) -> bytes:
    """ Encode a source as bytes using the UTF-8 codec, guaranteeing
        a proper return value without raising an error
    """
    if type(source) is bytes:
        return source
    elif type(source) is str:
        return u8encode(source)
    elif isinstance(source, six.string_types):
        return u8encode(source)
    elif isinstance(source, (int, float)):
        return u8encode(str(source))
    elif type(source) is bool:
        return source and b'True' or b'False'
    elif source is None:
        return b'None'
    return bytes(source)

def u8str(source: tx.Any) -> str:
    """ Encode a source as a Python string, guaranteeing a proper return
        value without raising an error
    """
    return u8bytes(source).decode(UTF8_ENCODING)

def stringify(instance: tx.Any, fields: tx.Iterable[str]) -> str:
    """ Stringify an object instance, using an iterable field list to
        extract and render its values, and printing them along with the 
        typename of the instance and its memory address -- yielding a
        repr-style string of the format:
        
            TypeName(fieldname="val", otherfieldname="otherval") @ 0x0FE
        
        The `stringify(…)` function is of use in `__str__()` and `__repr__()`
        definitions, E.G. something like:
        
            def __repr__(self):
                return stringify(self, type(self).__slots__)
        
    """
    field_dict: tx.Dict[str, str] = {}
    for field in fields:
        field_value = getattr(instance, field, "")
        field_value = callable(field_value) and field_value() or field_value
        if field_value:
            field_dict.update({ str(field) : field_value })
    field_dict_items: tx.List[str] = []
    for k, v in field_dict.items():
        field_dict_items.append(f'''{k}="{v}"''')
    typename: str = type(instance).__name__
    field_dict_string: str = ", ".join(field_dict_items)
    hex_id: str = hex(id(instance))
    return f"{typename}({field_dict_string}) @ {hex_id}"

def suffix_searcher(suffix: str) -> PredicateType:
    """ Return a boolean function that will search for the given
        file suffix in strings with which it is called, returning
        True when they are found and False when they aren’t.
        
        Useful in filter(…) calls and comprehensions, e.g.:
        
        >>> plists = filter(suffix_searcher('plist'), os.listdir())
        >>> mmsuffix = suffix_searcher('mm')
        >>> objcpp = (f for f in os.listdir() where mmsuffix(f))
    """
    import re, os
    if len(suffix) < 1:
        return lambda searching_for: True
    regex_str: str = r""
    if suffix.startswith(os.extsep):
        regex_str += rf"\{suffix}$"
    else:
        regex_str += rf"\{os.extsep}{suffix}$"
    searcher: PredicateType = re.compile(regex_str, re.IGNORECASE).search
    return lambda searching_for: bool(searcher(searching_for)) # type: ignore

def terminal_print(message: str,
                   handle: tx.IO = sys.stdout,
                   color: str = 'red',
                   asterisk: str = '*'):
    """ Print a string to the terminal, centered and bookended with asterisks
    """
    from clint.textui.colored import red  # type: ignore
    from clint.textui import colored      # type: ignore
    
    colorizer = getattr(colored, color.lower(), red)
    message: str = f" {message.strip()} "
    width: int = terminal_size().width
    
    asterisks: int = (width / 2) - (len(message) / 2)
    aa: str = asterisk[0] * asterisks
    ab: str = asterisk[0] * (asterisks + 0 - (len(message) % 2))
    
    print(colorizer(f"{aa}{message}{ab}"), file=handle)

def print_cache(BaseClass: tx.Type[type], cache_instance_name: str):
    """ Pretty-print the contents of a cached metaclass variable """
    from pprint import pprint
    
    instance: tx.Any = getattr(BaseClass, cache_instance_name)
    qualname: str = f"{BaseClass.__name__}.{cache_instance_name}"
    entrycnt: int = len(instance)
    dicttype: str = type(instance).__name__
    
    width: int = terminal_size().width
    
    print("=" * width)
    print("")
    print(f" • DUMPING METACLASS CACHE « {qualname}: {dicttype} »")
    print(f" • CACHE DICT HAS {entrycnt} ENTRIES{entrycnt > 0 and ':' or ''}")
    if entrycnt > 0:
        print("")
        pprint(instance, indent=4, depth=20,
                         width=width)
    print("")

def print_config(conf):
    """ Print debug information for a halogen.config.ConfigBase subclass """
    
    width: int = terminal_size().width
    
    print("=" * width)
    print("")
    print(f" • CONFIG: {conf.name}")
    print(f" • PREFIX: {conf.prefix}")
    print("")
    print("-" * width)
    
    print(" • INCLUDES:")
    print("")
    print(conf.get_includes())
    print("")
    print("-" * width)
    
    print(" • LIBS:")
    print("")
    print(conf.get_libs())
    print("")
    print("-" * width)
    
    print(" • CFLAGS:")
    print("")
    print(conf.get_cflags())
    print("")
    print("-" * width)
    
    print(" • LDFLAGS:")
    print("")
    print(conf.get_ldflags())
    print("")
    print("-" * width)
    
    print(" » stringification:")
    print("")
    print(str(conf))
    print("")
    # print("-" * width)

def test_compile(conf, test_source: str, print_cdb: bool = False) -> bool:
    """ Test-compile some inline C++ source, using the options provided
        by a given halogen.config.ConfigBase subclass instance.
    """
    import os
    
    if __package__ is None or __package__ == '':
        import config
        from compiledb import CDBBase
        from filesystem import NamedTemporaryFile, TemporaryName
    else:
        from . import config
        from .compiledb import CDBBase
        from .filesystem import NamedTemporaryFile, TemporaryName
    
    width: int = terminal_size().width
    bytelength: int = len(test_source)
    output: tx.Tuple[str, ...] = tuple()
    px: str = "yodogg-"
    cdb: CDBBase = CDBBase()
    
    print("=" * width)
    print("")
    print(f" • TESTING COMPILATION: config.CXX({conf.name}, "
           "<out>, <in>, cdb=CDBBase()) ...")
    print("")
    
    with NamedTemporaryFile(suffix="cpp",
                            prefix=px) as tf:
        
        tf.file.write(test_source)
        tf.file.flush()
        
        with TemporaryName(suffix="cpp.o",
                           prefix=px,
                           randomized=True) as adotout:
            
            print(f" ≠ C++ SOURCE: {tf.name} ({bytelength}b)")
            print(f" ≠ C++ TARGET: {adotout.name}")
            print("")
            
            output += config.CXX(conf, outfile=os.fspath(adotout), # type: ignore
                                       infile=os.fspath(tf),
                                       cdb=cdb,
                                       verbose=True)
            
            print("-" * width)
            
            if len(output[1]) > 0:
                # failure
                print(" * COMPILATION FAILED:")
                stdout: str = u8str(output[0]).strip()
                stderr: str = u8str(output[1]).strip()
                if stdout:
                    print(f"STDOUT: {stdout}", file=sys.stdout)
                    print("")
                if stderr:
                    print(f"STDERR: {stderr}", file=sys.stderr)
                    print("")
                return False
            
            # success!
            print(" • COMPILATION TOTALLY WORKED!")
            print("")
            cdb_json: str = str(cdb)
            stdout: str = u8str(output[0]).strip()
            stderr: str = u8str(output[1]).strip()
            if cdb_json and print_cdb:
                print(f"   CDB: {cdb_json}", file=sys.stdout)
                print("")
            if stdout:
                print(f" » STDOUT: {stdout}", file=sys.stdout)
                print("")
            if stderr:
                print(f" » STDERR: {stderr}", file=sys.stderr)
                print("")
            if adotout.exists:
                return True
            else:
                print("... BUT THEN WHERE THE FUCK IS MY SHIT?!?!")
    return False

def test():
    import os
    from pprint import pformat
    
    print("test memoized current_umask() * 3")
    assert current_umask() == current_umask()
    assert current_umask() == current_umask()
    assert current_umask() == current_umask()
    print("… success")
    
    def yo(dogg):
        return dogg.upper()
    
    yoyo = memoize(yo)
    print("test memoized function * 2*2")
    assert yoyo('dogg') == yoyo('dogg')
    assert yoyo('dogg') == yoyo('dogg')
    assert yoyo('doigg') == yoyo('doigg')
    assert yoyo('doigg') == yoyo('doigg')
    print("… success")
    
    print()
    print("-" * terminal_width)
    
    print(f"PACKAGE: {__package__}")
    # print(f" MODULE: {__module__})")
    print(f"   FILE: {__file__}")
    print(f"   SPEC: {__spec__}")
    relfile: str = os.path.relpath('/Users/fish/Dropbox/halogen/halogen/filesystem.py',
                                    start=os.path.dirname(__file__))
    print(f"RELFILE: {relfile}")
    
    ns = {
             'func' : lambda: print("Yo Dogg"),
        'otherfunc' : lambda string=None: print(string or 'no dogg.'),
          # '__all__' : ('func', 'otherfunc'),
          # '__dir__' : lambda: ['func', 'otherfunc']
    }
    
    modulize(ns, 'wat', "WHAT THE HELL PEOPLE", __file__)
    import wat # type: ignore
    
    # Call module functions:
    wat.func()
    wat.otherfunc("Oh, Dogg!")
    
    # Inspect module:
    # contents = ", ".join(sorted(wat.__dict__.keys()))
    contents: str = pformat(wat.__dict__, indent=4, width=terminal_size().width)
    print(f"Imported module name:      {wat.__name__}")
    print(f"Imported module contents:  {contents}")
    print(f"Imported module docstring: {wat.__doc__}")

if __name__ == '__main__':
    test()
