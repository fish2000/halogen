#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import collections
import collections.abc
import types
import typing as tx

if __package__ is None or __package__ == '':
    from utils import KeyValue, Originator, TypeAndBases, tuplize
else:
    from .utils import KeyValue, Originator, TypeAndBases, tuplize

__all__ = ('OCDType',
           'OCDSet', 'OCDFrozenSet',
           'OCDTuple', 'OCDList',
           'Namespace', 'SortedNamespace', 'OCDNamespace')

__dir__ = lambda: list(__all__)

T = tx.TypeVar('T', covariant=True)
S = tx.TypeVar('S', bound=str, covariant=True)
MaybeString = tx.Optional[str]
TypeFactory = tx.Callable[..., tx.Any]
MaybeFactory = tx.Optional[TypeFactory]
F = tx.TypeVar('F', bound=TypeFactory, covariant=True)

# ConcreteType = tx.TypeVar('ConcreteType', bound=type, covariant=True)
# NamedTupType = tx.TypeVar('NamedTupType', bound=tx.NamedTuple, covariant=True)
ClassGetType = tx.Callable[[tx._GenericAlias, tx.Tuple[type, ...]], # type: ignore
                            tx._GenericAlias]                       # type: ignore
PredicateType = tx.Callable[..., bool]
MaybePredicate = tx.Optional[PredicateType]

class OCDType(Originator):
    
    """ OCDType is a templated Python type.
    
        Literally, it is a subclass of `type`, allowing it to serve as a class
        factory, creating and customizing classes as do metaclasses. Unlike a
        typical Python metaclass, you directly engage with OCDType syntactically
        to create your subclass specializations.
        
        It’s called OCDType because its primary reason for being is it will sort
        its output iterators (at the time of writing we only use a vanilla call
        to the `sorted(…)` builtin, but I am sure you, like me, can envision a
        whole shmörgasbord of doodads and geegaws that would allow the twaddling
        and fine-tuning of all of those sort parameters.) It was written as a
        generalization of this one extremely stupidly simple class called OCDSet
        which extended the `set` builtin to intercept the output iterator and
        wrap it in a `sorted(…)`.
        
        But why use something dead-simple and functional, when you can spend a
        whole bunch more time generalizing the problem for no reason at all?
        Except for bragging rights maybe? In some mythical bar where many young,
        vivacious, attractive, scintillating Pythonistas of any and all genders
        imaginable congregate to regale one another of the various and sundry
        snippets of clever yet otherwise otioise code-morsels? This place does
        not exist, it is just you and me, and by you I mean this docstring and
        by me I mean me. Yes! Awesome. Anyway, as you were. Yes!
    """
    
    # The metaclass-internal name prefix, used to name generated
    # types, á la Objective-C naming prefixes:
    prefix: tx.ClassVar[str] = "OCD"
    
    # The metaclass-internal dictionaries of all generated types:
    types:    tx.ClassVar[tx.Dict[str, TypeAndBases]] = collections.OrderedDict()
    subtypes: tx.ClassVar[tx.Dict[str, TypeAndBases]] = collections.OrderedDict()
    
    @classmethod
    def __class_getitem__(metacls,
                         typename: tx.Union[type, tuple],
                          clsname: tx.Optional[str] = None,
                          factory: tx.Optional[TypeFactory] = None,
                        **kwargs) -> type:
        """ Specialize the template type OCDType on a given iterable type.
            Returns the newly specialized type, as per metaclass type creation.
        """
        from string import capwords
        if __package__ is None or __package__ == '':
            from utils import find_generic_for_type
        else:
            from .utils import find_generic_for_type
        
        # Validate covariant typevar argument:
        
        if not typename:
            raise KeyError("OCDType is a templated type, "
                           "it requires a Python type on which to specialize")
        if type(typename) == tuple:
            tup: tuple = tx.cast(tuple, typename)
            if len(tup) == 2:
                typename: type = tx.cast(type, tup[0])
                clsname: str = tx.cast(str, tup[1])
            elif len(tup) == 3:
                typename: type = tx.cast(type, tup[0])
                clsname: str = tx.cast(str, tup[1])
                factory: TypeFactory = tx.cast(TypeFactory, tup[2])
            elif len(tup) > 3:
                raise KeyError("Too many arguments passed to OCDType template "
                              f"specialization: {tup}")
        typename = tx.cast(type, typename)
        if not hasattr(typename, '__name__'):
            raise TypeError("OCDType is a templated type, "
                            "it must be specialized using a Python type "
                           f"(not a {type(typename)})")
        if typename.__name__ in metacls.types or \
           typename.__name__ in metacls.subtypes:
           raise TypeError("OCDType cannot be specialized on an "
                           "existant product of an OCDType specialization")
        if not hasattr(typename, '__iter__'):
            raise TypeError("OCDType is a templated type, "
                            "it must be specialized on an iterable Python type "
                           f"(not a {type(typename)})")
        
        # Save any passed clsname:
        
        clsnamearg: tx.Optional[str] = clsname and str(clsname) or None
        
        # Compute the name for the new class:
        
        if not clsname:
            name: str = capwords(typename.__name__)
            clsname = f"{metacls.prefix}{name}"
        elif not clsname.startswith(metacls.prefix):
            name: str = capwords(clsname)
            clsname = f"{metacls.prefix}{name}"
        
        if not clsname.isidentifier():
            raise KeyError("specialization class name must be a valid identifier "
                          f"(not “{clsname}”)")
        
        # If the class name already exists in the metaclass type dictionary,
        # return it without creating a new class:
        
        if clsname in metacls.types:
            return metacls.types[clsname].Type
        
        # Stow the covariant typevar and the computed name in the new class,
        # and install an `__iter__()` method that delegates to the covariant
        # implementation and wraps the results in a `sorted()` iterator before
        # returning them:
        
        # modulename: str = getattr(metacls, '__module__', 'ocd')
        modulename: str = metacls.prefix.lower()
        generic: type = find_generic_for_type(typename, missing=tx.Generic)
        unwrapped: ClassGetType = tx.Generic.__class_getitem__.__wrapped__
        get: ClassGetType = getattr(generic, '__class_getitem__',
                            getattr(generic, '__getitem__',
                            classmethod(
                            lambda cls, *args: unwrapped(cls, *args)))) # type: ignore
        params: tx.Tuple[tx.TypeVar, ...] = getattr(typename, '__parameters__',
                                            getattr(generic,  '__parameters__', tuple()))
        
        key: MaybePredicate = kwargs.pop('key', None)
        rev: bool = kwargs.pop('reverse', False)
        
        attributes: tx.Dict[str, tx.Any] = {
           '__class_getitem__' : get,
               '__covariant__' : typename,
                 '__generic__' : generic,
                  '__module__' : modulename,
                    '__name__' : clsname,
                    '__iter__' : lambda self: iter(
                                              sorted(typename.__iter__(self),
                                                     key=key,
                                                     reverse=rev)),
            
            # q.v. inline notes to the Python 3 `typing` module
            # supra: https://git.io/fAsNO
            
                    '__args__' : tuplize(typename),
              '__parameters__' : params,
            '__getitem_args__' : tuplize(typename, clsnamearg, factory),
                  '__origin__' : generic
        }
        
        # Using a factory -- a callable that returns an instance of the type,
        # á la “__new__” -- allows the wrapping of types like numpy.ndarray,
        # like so:
        #   
        #   OCDNumpyArray = OCDType[numpy.ndarray, 'OCDNumpyArray',
        #                           numpy.array]
        #   
        # … where “numpy.array(…)” is the factory function returning instances
        # of “numpy.ndarray”:
        
        if callable(factory):
            attributes.update({
                     '__new__' : lambda cls, *args, **kw: factory(*args, **kw), # type: ignore
                 '__factory__' : staticmethod(factory)
            })
        
        # Create the new class, as one does in the override of a
        # metaclasses’ __new__(…) method, and stash it in a
        # metaclass-local dict keyed with the generated classname:
        
        baseset: tx.List[type] = kwargs.pop('baseset', [])
        
        cls = type(clsname, tuplize(typename,
                                   *baseset,
                                    collections.abc.Iterable), # type: ignore
                            dict(attributes),
                          **kwargs)
        
        metacls.types[clsname] = TypeAndBases.for_type(cls)
        return cls
    
    def __new__(metacls,
                   name: str,
                  bases: tx.Iterable[type],
             attributes: tx.MutableMapping[str, tx.Any],
               **kwargs) -> type:
        """ When used as a metaclass, OCDType will insert a specialization
            of the class for which it has been chosen as a metaclass as its
            immediate base ancestor, and then create a new class based
            on that specialization for forwarding to Python’s class-creation
            apparatus:
        """
        if name in metacls.subtypes:
            return metacls.subtypes[name].Type
        
        subbase: type = object
        for basecls in bases:
            if issubclass(basecls, (tx.Iterable,
                                    tx.Iterator)):
                subbase = basecls
                break
        
        # DON’T KNOW ABOUT YOU BUT I AM UN:
        debaser: tx.Tuple[type, ...] = tuplize(subbase,
                                               collections.abc.Iterable, # type: ignore
                                               collections.abc.Iterator) # type: ignore
        
        subname: MaybeString = kwargs.pop('subname', None)
        factory: MaybeFactory = kwargs.pop('factory', None)
        key: MaybePredicate = kwargs.pop('key', None)
        rev: bool = kwargs.pop('reverse', False)
        
        baseset: tx.List[type] = [chien for chien in bases if chien not in debaser]
        
        # Create the base ancestor with a direct call to “__class_getitem__(…)”
        # -- which, note, will fail if no bases were specified; if `subbase`
        # defaults to “object”, this call will raise a TypeError, as it requires
        # an iterable operand:
        base = metacls.__class_getitem__(subbase,
                                         subname,
                                         factory, key=key,
                                                  reverse=rev,
                                                  baseset=baseset,
                                       **kwargs)
        
        # The return value of type.__new__(…), called with the amended
        # inheritance-chain values, is what we pass off to Python:
        cls = super().__new__(metacls, name, # type: ignore
                                       tuplize(base),
                                       dict(attributes),
                                     **kwargs)
        
        metacls.subtypes[name] = TypeAndBases.for_type(cls)
        return cls

###
### SPECIALIZATIONS OF OCDType:
###

OCDSet        = OCDType[set]                        # type: ignore
OCDFrozenSet  = OCDType[frozenset, 'OCDFrozenSet']  # type: ignore
OCDTuple      = OCDType[tuple]                      # type: ignore

class SortedList(list, metaclass=OCDType):
    """ Generic class, accepts a type parameter """
    pass

# this emits the cached type from above:
OCDList       = OCDType[list] # type: ignore

class Namespace(KeyValue[S, T], types.SimpleNamespace):
    __slots__ = tuple()
    
    """ Generic class, accepts two type parameters: """
    
    def __bool__(self) -> bool:
        return bool(self.__dict__)
    
    def __iter__(self) -> tx.Iterator[T]:
        return iter(self.__dict__)
    
    def __len__(self) -> int:
        return len(self.__dict__)
    
    def __contains__(self, key: S) -> bool:
        return key in self.__dict__
    
    def __repr__(self) -> str:
        keys = sorted(self.__dict__, key=lambda k: str(k))
        items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
        return "{}({})".format(type(self).__name__, ", ".join(items)) # type: ignore


class SortedNamespace(Namespace[str, T], collections.abc.MutableMapping,
                                         collections.abc.Iterable,
                                         collections.abc.Sized,
                                         metaclass=OCDType):
    __slots__ = tuple()
    
    """ Generic class, accepts one type parameter: """
    
    def __getitem__(self, key: str) -> T:
        if key in self.__dict__:
            return self.__dict__[key]
        return super().__getattr__(key) # type: ignore
    
    def __setitem__(self, key: str, value: T):
        if not key.isidentifier():
            raise KeyError("key must be a valid identifier")
        super().__setattr__(key, value)

# Also generic, with two type params
OCDNamespace  = OCDType[Namespace] # type: ignore


def test_namespace_types():
    """ Test instances of various SimpleNamespace subclasses """
    
    from pprint import pformat
    if __package__ is None or __package__ == '':
        from utils import terminal_size
    else:
        from .utils import terminal_size
    
    nsdata: tx.Dict[str, str] = {
                'yo' : 'dogg',
                 'i' : 'heard',
               'you' : 'liked',
        'namespaced' : 'dictionary data'
    }
    
    simpleNamespace: types.SimpleNamespace = types.SimpleNamespace(**nsdata)
    namespace: Namespace[str, str] = Namespace(**nsdata)
    ocdNamespace: OCDNamespace[str, str] = OCDNamespace(**nsdata)
    sortedNamespace: SortedNamespace[str] = SortedNamespace(**nsdata)
    width: int = terminal_size().width
    
    print("=" * width)
    print("")
    
    print("• SIMPLE NAMESPACE: ")
    print(pformat(simpleNamespace,
                  indent=4, depth=10, width=width))
    print("")
    
    print("• REGULAR NAMESPACE: ")
    print(pformat(namespace,
                  indent=4, depth=10, width=width))
    print("")
    
    print("• OCD NAMESPACE: ")
    print(pformat(ocdNamespace,
                  indent=4, depth=10, width=width))
    print("")
    
    print("• SORTED NAMESPACE: ")
    print(pformat(sortedNamespace,
                  indent=4, depth=10, width=width))
    print("")

def test():
    """ Inline tests for OCDType and friends """
    
    from pprint import pprint
    if __package__ is None or __package__ == '':
        from utils import print_cache
    else:
        from .utils import print_cache
    
    """ 0. Set up some specializations and subtypes for testing: """
    
    import array
    OCDArray      = OCDType[array.array]
    
    import numpy # type: ignore
    OCDNumpyArray = OCDType[numpy.ndarray, 'OCDNumpyArray',
                            numpy.array]
    
    class SortedMatrix(numpy.matrix, metaclass=OCDType,
                                     subname='OCDMatrix',
                                     factory=numpy.asmatrix,
                                     key=lambda x: abs(x), reverse=True): pass
    
    OCDMatrix     = OCDType[numpy.matrix]
    
    ocd_settttts  = OCDType[set]
    
    """ 1. Assert-check properties of specializations and subtypes: """
    
    assert ocd_settttts == OCDSet
    assert ocd_settttts.__name__ == 'OCDSet'
    assert ocd_settttts.__base__ == set
    assert not hasattr(ocd_settttts, '__factory__')
    assert ocd_settttts.__generic__ == tx.Set
    
    assert OCDSet[T]
    assert OCDSet[str]
    assert SortedList[T]        # this is generic because find_generic_for_type() works for `list`
    assert SortedNamespace[T]   # this is generic because it inherits from all my crazy `utils` shit
    assert OCDArray[T]
    assert OCDNumpyArray[T]
    assert OCDMatrix[T]
    assert SortedMatrix[T]      # this is generic because I fixed `utils.Originator.__getitem__(…)`
    
    assert OCDMatrix.__generic__ == tx.Generic
    
    pprint(SortedMatrix.__mro__)    # (__main__.test.<locals>.SortedMatrix,
                                    # <class 'ocd.OCDMatrix'>,
                                    # <class 'numpy.matrixlib.defmatrix.matrix'>,
                                    # <class 'numpy.ndarray'>,
                                    # <class 'collections.abc.Iterable'>,
                                    # <class 'object'>)
    
    pprint(OCDMatrix.__mro__)       # (<class 'ocd.OCDMatrix'>,
                                    # <class 'numpy.matrixlib.defmatrix.matrix'>,
                                    # <class 'numpy.ndarray'>,
                                    # <class 'collections.abc.Iterable'>,
                                    # <class 'object'>)
    
    pprint(OCDNumpyArray.__mro__)   # (<class 'ocd.OCDNumpyArray'>,
                                    # <class 'numpy.ndarray'>,
                                    # <class 'collections.abc.Iterable'>,
                                    # <class 'object'>)
    
    print()
    
    # pprint(SortedMatrix.__parameters__)
    # pprint(OCDMatrix.__parameters__)
    # pprint(OCDNumpyArray.__parameters__)
    # pprint(SortedMatrix.__args__)
    # pprint(OCDMatrix.__args__)
    # pprint(OCDNumpyArray.__args__)
    
    try:
        # Generics take only one type parameter:
        print(type(OCDSet[T, S]))
    except TypeError as exc:
        assert 'Too many parameters' in str(exc)
    else:
        assert False, "`OCDSet[T, S]` didn’t raise!"
    
    pprint(OCDSet[T])           # typing.Set[+T]
    pprint(OCDFrozenSet[T])     # typing.FrozenSet[+T]
    pprint(OCDArray[T])         # typing.Generic[+T]
    pprint(OCDNumpyArray[T])    # typing.Generic[+T]
    pprint(OCDMatrix[T])        # typing.Generic[+T]
    pprint(OCDTuple[T, ...])    # typing.Tuple[+T, ...]
    pprint(OCDTuple[T])         # typing.Tuple[+T]
    pprint(OCDTuple[T, S])      # typing.Tuple[+T, +S]
    pprint(OCDList[T])          # typing.List[+T]
    pprint(SortedList[T])       # ocd.OCDList[~T] (PHEW.)
    pprint(SortedNamespace[T])  # __main__.SortedNamespace[+T]
    pprint(SortedMatrix[T])     # __main__.test.<locals>.SortedMatrix[+T]
    
    print()
    
    pprint(OCDSet[T])
    pprint(OCDSet.__origin__)
    pprint(OCDSet.__generic__)
    pprint(OCDSet[T].__origin__)
    
    print()
    
    pprint(SortedList[T])
    pprint(SortedList.__origin__)
    pprint(SortedList.__generic__)
    pprint(SortedList[T].__origin__)
    
    print()
    
    pprint(OCDList[T])
    pprint(OCDList.__origin__)
    pprint(OCDList.__generic__)
    pprint(OCDList[T].__origin__)
    
    print()
    
    pprint(OCDNamespace[S, T])
    pprint(OCDNamespace.__origin__)
    pprint(OCDNamespace.__generic__)
    pprint(OCDNamespace[S, T].__origin__)
    
    print()
    
    pprint(SortedNamespace[T])
    pprint(SortedNamespace.__origin__)
    pprint(SortedNamespace.__generic__)
    pprint(SortedNamespace[T].__origin__)
    
    assert OCDNumpyArray.__name__ == 'OCDNumpyArray'
    assert OCDNumpyArray.__base__ == numpy.ndarray
    assert OCDNumpyArray.__bases__ == tuplize(numpy.ndarray,
                                              collections.abc.Iterable)
    assert OCDNumpyArray.__factory__ == numpy.array
    assert OCDNumpyArray.__generic__ == tx.Generic
    
    assert SortedMatrix.__base__ == OCDType[numpy.matrix]
    assert SortedMatrix.__base__.__name__ == 'OCDMatrix'
    assert SortedMatrix.__base__.__base__ == numpy.matrixlib.defmatrix.matrix
    assert SortedMatrix.__base__.__factory__ == numpy.asmatrix
    assert SortedMatrix.__base__.__generic__ == tx.Generic
    
    assert OCDArray('i', range(10)).__len__() == 10
    assert numpy.array([[0, 1, 2], [0, 1, 2], [0, 1, 2]]).__len__() == 3
    assert OCDNumpyArray([[0, 1, 2], [0, 1, 2], [0, 1, 2]]).__len__() == 3
    assert SortedMatrix([[0, 1, 2], [0, 1, 2], [0, 1, 2]]).__len__() == 3
    assert SortedMatrix(OCDNumpyArray([[0, 1, 2], [0, 1, 2], [0, 1, 2]])).__len__() == 3
    
    try:
        # can’t specialize a specialization!
        OCDType[OCDSet]
    except TypeError as exc:
        assert "specialization" in str(exc)
    else:
        assert False, "`OCDType[OCDSet]` didn’t raise!"
    
    """ 2. Test various SimpleNamespace subclasses: """
    
    test_namespace_types()
    
    """ 3. Reveal the cached OCDType specializations: """
    
    assert len(OCDType.types) == 8
    print_cache(OCDType, 'types')
    
    """ 4. Reveal the cached OCDType subtypes: """
    
    assert len(OCDType.subtypes) == 3
    print_cache(OCDType, 'subtypes')
    
    
    # class Base(object):
    #     def __init__(self):
    #         self.base = "in your base"
    #     def yodogg(self):
    #         return "i heard you liked attrs"
    #
    # class Derived(Base):
    #
    #     def doggyo(self):
    #         # return getattr(super(), 'base')
    #         # return super().base
    #         f = getattr(super(), 'yodogg')
    #         return f()
    #
    # d = Derived()
    # print(d.doggyo())
    
    class Descriptor(object):
        
        __slots__ = tuplize('name')
        
        def __init__(self, *args, **kwargs):
            pass
        
        def __get__(self, instance, cls=None):
            if cls is None:
                cls = type(instance)
        
        def __set__(self, instance, value):
            pass
        
        def __delete__(self, instance):
            pass
        
        def __set_name__(self, cls, name):
            self.name = name
    
    class NewType:
    
        """NewType creates simple unique types with almost zero runtime
        overhead. `NewType(name, tp)` is considered a subtype of `tp`
        by static type checkers. At runtime, NewType(name, tp) creates
        a callable instance that simply returns its argument when called.
        Usage::

            UserId = NewType('UserId', int)

            def name_by_id(user_id: UserId) -> str:
                ...

            UserId('user')          # Fails type check

            name_by_id(42)          # Fails type check
            name_by_id(UserId(42))  # OK

            num = UserId(5) + 1     # type: int
        """
    
        __slots__ = ('__name__',
                     '__qualname__',
                     '__supertype__')

        def __init__(self, name, tp):
            self.__name__ = self.__qualname__ = name
            self.__supertype__ = tp

        @staticmethod
        def __call__(arg):
            return arg

        def __repr__(self):
            return f"{type(self).__name__}<" \
                   f"{self.__qualname__}:" \
                   f"{self.__supertype__.__name__}>"

        def __hash__(self):
            return hash((self.__name__, self.__supertype__))
    
    
    YoDogg = NewType('YoDogg', str)
    YouLikeInts = NewType('YouLikeInts', int)
    
    def DoggPrinter(arg: YoDogg) -> YoDogg:
        print(tx.cast(str, arg))
        return arg
    
    def DoggEvaluator(arg: YouLikeInts) -> int:
        intarg = tx.cast(int, arg)
        print(f"Integer argument: {intarg}")
        return intarg
    
    dogg: YoDogg = YoDogg('Dogg, Yo!')
    DoggPrinter(dogg)
    
    inyour: YouLikeInts = YouLikeInts(666)
    DoggEvaluator(inyour)
    
    print(repr(YoDogg))
    print(repr(YouLikeInts))
    
if __name__ == '__main__':
    test()
