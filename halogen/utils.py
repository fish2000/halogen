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
    """ Return a new tuple containing all non-`None` arguments """
    return tuple(item for item in items if item is not None)

def listify(*items) -> tx.List[tx.Any]:
    """ Return a new list containing all non-`None` arguments """
    return list(item for item in items if item is not None)

class GenericAlias(tX._GenericAlias, _root=True):
    """ `utils.GenericAlias` is a re-wrapped and sugar-coated user-facing
        descendant of the `typing._GenericAlias` class.
        
        It directly inherits from `typing._GenericAlias` – the foundational
        class of the `typing` module – and exposes this very useful part of
        the `typing` API’s implementation details.
        
        The extensive `__repr__` implementation is a far more complete and
        generically useful version of the `typing._GenericAlias.__repr__(…)`
        mechanism – it completely replaces the ancestor funtionality without
        making any `super()` calls. 
        
        Our `utils.GenericAlias` also furnishes `copy_with(…)` – q.v. the
        `typing._GenericAlias` method supra. – and offers the user a class
        method `alias(…)` that works much like the private `typing._alias`
        helper function.
        
        (Note that `__init__` has not been overriden, preserving the core
        of the ancestor behavior mechanisms.)
    """
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
        """ This method works almost exactly like the ancestor method
            of the same name, with the notable exception that the type
            of instance returned is dynamically determined instead of
            hard-coded to a specific class. 
        """
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
    """ The Originator metaclass assists in creating generics.
        
        As the name suggests, it will attempt to discern the best value
        to use for an “__origin__” class-level value during class creation.
        
        It imbues those classes for which it is meta with `__origin__`,
        a class-based `__repr__` (based on the ``typing._type_repr`` internal
        helper function), and a class-based `__getitem__` implementation
        that leverages `utils.GenericAlias` (q.v. class definition supra.)
        
        Additionally, it exports the `abc.abstractmethod` decorator in the
        attribute namespace of the classes it creates, renaming it `abstract`
        for your convenience; one can decorate methods as `@abstract` without
        bothering to import from `abc` or write out the full cumbersome  name
        `@abc.abstractmethod` every time… YOU’RE WELCOME
    """
    
    @staticmethod
    def type_repr(obj: tx.Any) -> str:
        """ Adapted from `_type_repr(…)`, an internal helper function
            from the “typing” module. This implementation extends the
            functionality of the original through the use of `inspect`
            to ascertain the module from which the object to be repr’d
            is definitively known.
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
        """ A default class-based `__repr__` implementation using `type_repr()`
            (q.v. static method implemenation supra.)
        """
        return cls.type_repr(cls)
    
    def __getitem__(cls,
                 params: tx.Union[tx.TypeVar,
                                  tx.Iterable[tx.TypeVar]]) -> GenericAlias:
        """ A wrapper method for getting a GenericAlias instance
            through calls to the generic version of the `__origin__` class
            method for “specialization” (aka. the generics’ `__getitem__`
            or `__class_getitem__` method).
            
            Internally, the `__getitem__` or `__class_getitem__` call is
            probed for a wrapper decorator, which if present is circumvented
            through any `__wrapped__` attribute value. The `inspect` module
            is then used to examine the signature of the call, and arguments
            are configured as needed. 
            
            Any instances of `typing._GenericAlias` returned through this
            process is itself examined, and the results are upgraded to
            a `utils.GenericAlias` instance value to then be returned.
        """
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
    """ A generic key-value ancestor class.
        
        Both the key type and the value type are covariant, and must
        be specified by child inheritors of `KeyValue`. Subclasses
        may choose to either employ fixed parameter names via `__slots__`,
        or may instead eschew these in favor of the default attribute
        instance-dictionary mechanism.
        
        Subclasses will automatically have an `__origin__` value set
        for them via the `__init_subclass__` hook; subclasses defining
        `__init_subclass__` for themselves must make a call to the ancestor
        implementation:
        
            super().__init_subclass() # NO ARGS OR KWARGS IN SUPER CALL
        
        A class-level `__repr__` is included, with the implementation
        making use of the static method `Originator.type_repr()` (q.v.
        method definition supra.)
    """
    __slots__: tx.Tuple[str, ...] = tuple()
    
    @classmethod
    def __repr__(cls) -> str:
        """ Since `utils.KeyValue` does not use `utils.Originator` as
            its metaclass, we delegate `__repr__(…)` directly to the
            `utils.Originator.type_repr(¬)` class method.
        """
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
    """ A generic abstract base class for defining namespaces.
        
        Concrete implementors of the Namespace abstract class require
        method definitions for `__bool__(self)`, `__len__(self)`,
        `__contains__(self, T)`, and most importantly `__iter__(self)`.
        
        The methods `__bool__` and `__contains__` return “bool” types,
        `__len__` of course returns an “int” type, and the `__iter__`
        method must return an iterator yielding instances of this
        Namespace’s value type – specifically `typing.Iterator[U]`
        is the `__iter__` methods’ return type.
        
        Also required is a `__repr__(self) -> str` method definition,
        and an implementation for `get(self, T, value[T])` which
        returns `typing.Optional[U]` – a value type instance or `None`.
    """
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
    """ A generic, concrete namespace class that implements several
        abstract interfaces; most notably `utils.Namespace` (q.v.
        abstract base class definition supra.)
    
        In addition to `utils.Namespace`, `DictNamespace` furnishes
        implementations for `typing.MutableMapping`, `typing.Sized`,
        `typing.Iterable`, and `typing.Container`.
        
        The mechanism of `DictNamespace` exposes many of attributes
        and methods of the instances’ internal `__dict__`. Since
        the internal `__dict__` is specified as a `__slots__` entry,
        any subclasses of `DictNamespace` can safely define their own
        `__slots__` values in order to distinguish between instance
        attributes used in implementations, and those that comprise
        the data payload of those instances.
    """
    __slots__: tx.Tuple[str, ...] = tuplize('__dict__')
    
    def __init__(self, **kwargs):
        """ Initialize a new DictNamespace instance, optionally
            passing initial namespace values as keyword arguments:
        """
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
    """ This SimpleNamespace class has functionality and semantics
        analogous to `types.SimpleNamespace`; it is generic in its
        covariant value type, and enforces the use of string values
        in its invariant key type.
    """
    __slots__: tx.Tuple[str, ...] = tuple()

class MultiNamespace(Namespace[str, T], MultiMap[str, T],
                                        tx.MutableMapping[str, T],
                                        tx.Collection[T]):
    """ A generic, concrete namespace class, based on ``MultiDict``,
        a one-key-to-many-values dictionary class from the eponymous
        `multidict` module (q.v. https://github.com/aio-libs/multidict
        module code GitHub repo sub.) implementing several abstract
        interfaces; most notably `utils.Namespace` (q.v. abstract base
        class definition supra.) and `multidict._abc.MultiMapping`.
        
        Besides `utils.Namespace` and `multidict._abc.MultiMapping`,
        `MultiNamespace` furnishes implementations for the
        `typing.MutableMapping` and `typing.Collection` abstract
        generic base classes (the latter of which implicitly includes
        the `typing.Sized`, `typing.Iterable`, and `typing.Container`
        interface requirements).
        
        `MultiNamespace` stores its `multidict.MultiDict` instance
        in a `__slots__`-based attribute; `MultiNamespace` instances
        use the `multidict.MultiDict` instance value much as its
        class-heirarchy sibling `utils.DictNamespace` employs the
        instance `__dict__`. 
        
        In addition to the required methods, this class also furnishes
        a handful of its own one-off methods that specifically pertain
        to the multiple-value-mapping paradigm: `count(¬T)`, `getone(¬T)`,
        `getall(¬T)`, and `zero(¬T)` allow multiple values to be queried
        and accessed. 
        
        The internally-used `mdict()` method is unobfuscatedly exposed,
        allowing the instances’ underlying `multidict.MultiDict` to be
        directly manipulated by users.
    """
    __slots__: tx.Tuple[str, ...] = tuplize('_dict',
                                            '_initialized')
    
    def __init__(self, **kwargs):
        """ Initialize a new MultiNamespace instance, optionally
            passing initial namespace values as keyword arguments:
        """
        self._dict: MutableMultiMap[str, T] = MultiDict()
        self._dict.update(kwargs)
        self._initialized: bool = True
    
    def initialized(self) -> bool:
        """ Returns a boolean indicating whether or not the instance
            has been successfully initialized – defined by whether or
            not the `__init__` method has finished running.
        """
        try:
            return super().__getattribute__('_initialized')
        except:
            return False
    
    def mdict(self) -> MutableMultiMap[str, T]:
        """ Return a reference to the `MultiNamespace` instances’
            internal `multidict.MultiDict`.
        """
        return super().__getattribute__('_dict')
    
    def __bool__(self) -> bool:
        """ The namespace is truthy if it contains one or more
            key-value pairs, and falsey if it is empty.
        """
        return bool(self.mdict())
    
    def __len__(self) -> int:
        """ The namespaces’ length is equal to the number of
            individual keys it contains (irrespective of how
            many values are associated with any of those keys).
        """
        return len(self.mdict())
    
    def __contains__(self, key: str) -> bool:
        """ A namespace contains a key if that key has at least
            one value associated with it.
        """
        return key in self.mdict()
    
    def __getitem__(self, key: str) -> T:
        """ Return the namespace value most recently associated
            with the given key.
        """
        return self.mdict()[key]
    
    def __setitem__(self, key: str, val: T):
        """ Associate a new value with a given key, preserving
            any of namespace values that were added previously.
        """
        self.mdict()[key] = val
    
    def __delitem__(self, key: str):
        """ Delete all values associated with a given key. """
        del self.mdict()[key]
    
    def __iter__(self) -> tx.Iterator[T]:
        """ Return an iterator over a flattened dict containing
            the namespaces’ keys associated with each of the values
            most recently added for that key.
        """
        return iter(dict(self.mdict()))
    
    def __getattr__(self, key: str) -> T:
        return self.getone(key)
    
    def __setattr__(self, key: str, val: T):
        if self.initialized():
            self.mdict().add(key, val)
        else:
            super().__setattr__(key, val)
    
    def add(self, key: str, val: T):
        """ Associate a new value with a given key, preserving
            any of namespace values that were added previously.
        """
        self.mdict().add(key, val)
    
    def getone(self, key: str) -> T:
        """ Return the namespace value most recently associated
            with the given key.
        """
        return self.mdict().getone(key)
    
    def getall(self, key: str) -> tx.Tuple[T, ...]:
        """ Return a tuple populated with all namespace values
            that are associated with a given key.
        """
        return self.mdict().getall(key)
    
    def get(self, key: str,
        default_value: tx.Optional[T] = None) -> tx.Optional[T]:
        """ Return either the value most recently associated with a
            given key, or a default value if no values are found. 
        """
        return (key in self.mdict()) and self.getone(key) or default_value
    
    def count(self, key: str) -> int:
        """ Query the namespace for the number of values that
            are associated with a given key.
        """
        return (key in self.mdict()) and len(self.getall(key)) or 0
    
    def zero(self, key: str) -> bool:
        """ Remove all values associated with the given key
            from the namespace instance.
        """
        if key in self.mdict():
            del self.mdict()[key]
            return True
        return False
    
    def __copy__(self):
        """ Return a shallow copy of the `MultiNamespace` instance. """
        out = type(self)()
        out.mdict().update(self.mdict())
        return out
    
    def __repr__(self) -> str:
        """ The `MultiNamespace` representation is the same as that
            of its internal `multidict.MultiDict` instance.
        """
        return repr(self.mdict())

ConcreteType = tx.TypeVar('ConcreteType', bound=type, covariant=True)
CT = tx.TypeVar('CT', bound=type, covariant=True)
BaseType = tx.TypeVar('BaseType', covariant=True)
BT = tx.TypeVar('BT', bound=type, covariant=True)
NewTypeCallable = tx.Callable[[BaseType], BaseType]

class NamedTupleMeta(tx.NamedTupleMeta):
    """ An extension of the `typing.NamedTupleMeta` metaclass that
        sets the `__origin__` value on those classes it creates,
        per the base classes of the newly created class.
    """
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
    """ A public version of the `typing.NamedTuple` class that utilizes
        `utils.NamedTupleMeta` to establish an `__origin__` class value.
    """
    _root: tx.ClassVar[bool] = True

class TypeAndBases(NamedTuple):
    """ A typed NamedTuple subclass for storing a type plus a list
        of the stringified names of all of its bases:
    """
    Type:   tx.Type[ConcreteType]
    Name:   str
    Bases:  tx.List[str] = []
    
    @classmethod
    def for_type(cls,
              newcls: tx.Type[ConcreteType]) -> "TypeAndBases":
        """ A convenient class method for obtaining a populated
            `utils.TypeAndBases` instance from a class, filling in
            values for `Name` and `Bases` per that class value.
        """
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
    """ A `TypeSpace` instance correlates classes both by the name
        and the value of their origin classes. 
        
        The original use-case of the `TypeSpace` namespace was to
        provide a way to look up the generic version of a concrete
        (and likely built-in) Python class, e.g.:
        
            types = TypeSpace()
            types.add_generics_from_module(typing)
            ListT = typing.List
            
            assert types.list == ListT              # lookup by name
            assert types.for_origin[list] == ListT  # lookup by type
            assert ListT.__origin__ == list         # confirm origin
        
        … `TypeSpace` namespaces require that a type is either an
       “original type” (with an `__origin__` pointing to one of
        its bases) or a generic type, whose `__origin__` points to
        a corresponding non-generic concrete type. Depending on
        how `__origin__` is used, one adds the type to a `TypeSpace`
        instance through a call to either `add_original(cls)` or
        `add_generic(cls)`. Either way, `__origin__` must be set
        on the type to something valid.
        
        A method wrapping `typing.NewType` is provided, for creating
        a new type while properly add it to the `TypeSpace` instance,
        predictably named `NewType(…)` with the same signature as
        the `typing` module function; `NewTypeMember(…)` does the same
        thing but further wraps the new type as a `staticmethod()`,
        allowing the returned new types to be used as class members
        without any `self`-passing arity issues cropping up.
    """
    
    __slots__: tx.Tuple[str, ...] = tuplize('for_origin')
    
    def __init__(self, **kwargs):
        """ Initialize a new TypeSpace instance, optionally passing
            initial namespace values as keyword arguments:
        """
        self.for_origin: DictNamespace[CT, BT] = DictNamespace()
        super().__init__(**kwargs)
    
    def add_original(self, cls: tx.Any) -> bool:
        """ Add an original (non-generic) class to the TypeSpace instance.
            The class being addded to the TypeSpace must posess a meaningful
            accessible class-variable “__origin__” value.
        """
        origin: tx.Optional[CT] = getattr(cls, '__origin__', None)
        if not origin:
            return False
        self.for_origin[cls] = origin
        self.add(cls.__name__, origin)
        return True
    
    def add_generic(self, cls: tx.Any) -> bool:
        """ Add a generic class to the TypeSpace instance. """
        origin: tx.Optional[CT] = getattr(cls, '__origin__', None)
        if not origin:
            return False
        self.for_origin[origin] = cls
        self.add(origin.__name__, cls)
        return True
    
    def add_generics_from_module(self, module: types.ModuleType) -> int:
        """ Add all the generic classes exported from a given module.
            The module’s members are enumerated with `dir()` and as such
            no private or unexported members of the module will be added.
        """
        generic_count: int = 0
        for key in dir(module):
            modattr = getattr(module, key)
            if self.add_generic(modattr):
                generic_count += 1
        return generic_count
    
    def NewType(self,
                name: str,
            basetype: tx.Type[BT]) -> NewTypeCallable:
        """ Wraps typing.NewType(…) in a function that
            a) sets __origin__ on the returned new-type factory function, and
            b) stores the new-type factory in the TypeSpace instance. 
        """
        func: NewTypeCallable = tx.NewType(name, basetype)
        func.__origin__ = basetype
        basename: str = basetype.__name__
        self.for_origin[basetype] = func
        self.add(basename, func)
        return func
    
    def NewTypeMember(self,
                      name: str,
                  basetype: tx.Type[BT]) -> NewTypeCallable:
        """ Returns the value of TypeSpace.NewType(self, …) wrapped in a
            call to staticmethod(), allowing the return value to be bound
            to a class-variable instance without any “self”-passing issues.
        """
        return staticmethod(self.NewType(name, basetype))

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
    """ Find the generic version of a type.
        
        An optional default return value specifies what to return if
        no generic type is found to correspond to a given type; if
        this value is unspecified, `None` is returned for types for
        which no generics can be found.
        
        Currently, generic types are limited to what the `typing` module
        defines as exports. So `find_generic_for_type(list)` returns
        `typing.List`, but `find_generic_for_type(numpy.ndarray)` will
        not magically conjure a generic Numpy array type.
    """
    if not hasattr(cls, '__mro__'):
        return missing
    for t in cls.__mro__:
        if t in ty.for_origin:
            return ty.for_origin.get(t)
    return missing


class TerminalSize(object):
    
    class Size(tx.NamedTuple):
        
        height: int = 25
        width: int = 105
        
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
    
    Descriptor = ty.NewTypeMember('Descriptor', int)
    
    DEFAULT_LINES:   int = 25
    DEFAULT_COLUMNS: int = 105
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
        Descriptor = self.Descriptor
        
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
        descriptor: Descriptor = Descriptor(0)
        if not sz:
            try:
                descriptor = os.open(os.ctermid(),
                                     os.O_RDONLY)
                sz = self.ioctl_GWINSZ(descriptor)
            except:
                pass
            finally:
                if descriptor:
                    os.close(tx.cast(int,
                                     descriptor))
        
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
