# -*- coding: utf-8 -*-

from __future__ import print_function

import abc
import collections
import collections.abc
import types
import typing as tx

# from functools import partial, partialmethod
from utils import find_generic_for_type, tuplize, u8str

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

ClassGetType = tx.Callable[[tx._GenericAlias, tx.Tuple[type, ...]],
                            tx._GenericAlias]


class OCDType(abc.ABCMeta, tx.Iterable[T]):
    
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
    prefix: str = "OCD"
    
    class TypeAndBases(tx.NamedTuple):
        Type:   tx.Type[type]
        Bases:  tx.Tuple[str, ...] = ()
        
        @classmethod
        def for_type(cls, newcls):
            basenames = []
            for base in newcls.__bases__:
                name = getattr(base, '__qualname__',
                       getattr(base, '__name__'))
                mod = getattr(base, '__module__', '')
                if len(mod) > 1:
                    mod += '.'
                basenames.append(f"{mod}{name}")
            return cls(newcls, tuple(basenames))
    
    # The metaclass-internal dictionaries of all generated types:
    types:    tx.Dict[str, TypeAndBases] = collections.OrderedDict()
    subtypes: tx.Dict[str, TypeAndBases] = collections.OrderedDict()
    
    @classmethod
    def __class_getitem__(metacls,
                              key: tx.Union[type, tuple],
                          clsname: tx.Optional[str] = None,
                          factory: tx.Optional[TypeFactory] = None,
                        **kwargs) -> type:
        """ Specialize the template type OCDType on a given iterable type.
            Returns the newly specialized type, as per metaclass type creation.
        """
        from string import capwords
        
        # Validate covariant typevar argument:
        
        if not key:
            raise KeyError("OCDType is a templated type, "
                           "it requires a Python type on which to specialize")
        if type(key) == tuple:
            tup: tx.Tuple = tx.cast(tx.Tuple, key)
            if len(tup) == 2:
                key, clsname = tup
            elif len(tup) == 3:
                key, clsname, factory = tup
            elif len(tup) > 3:
                raise KeyError("Too many arguments passed to OCDType template "
                               "specialization: {tup}")
        if key.__name__ in metacls.types or \
           key.__name__ in metacls.subtypes:
           raise TypeError("OCDType cannot be specialized on an "
                           "existant product of an OCDType specialization")
        if type(key) != type:
            raise TypeError("OCDType is a templated type, "
                            "it must be specialized using a Python typevar "
                           f"(not a {type(key)})")
        if not hasattr(key, '__iter__'):
            raise TypeError("OCDType is a templated type, "
                            "it must be specialized on an iterable Python type "
                           f"(not a {type(key)})")
        
        # Save any passed clsname:
        
        clsnamearg: tx.Optional[str] = clsname and str(clsname) or None
        
        # Compute the name for the new class:
        
        if not clsname:
            name: str = capwords(key.__name__)
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
        
        it: tx.Iterable = tx.cast(tx.Iterable, key)
        modulename: tx.Optional[str] = getattr(metacls, '__module__', '__main__')
        generic: tx.Optional[type] = find_generic_for_type(key, missing=tx.Generic)
        get: ClassGetType = getattr(generic, '__class_getitem__',
                            getattr(generic, '__getitem__',
                                    lambda cls, *args, **kw: cls))
        
        attributes: tx.Dict[str, tx.Any] = {
           '__class_getitem__' : get,
               '__covariant__' : key,
                 '__generic__' : generic,
                  '__module__' : modulename,
                    '__name__' : clsname,
                    '__iter__' : lambda self: iter(sorted(it.__iter__(self))),
            
            # q.v. inline notes to the Python 3 `typing` module
            # supra: https://git.io/fAsNO
            
                    '__args__' : tuplize(key, clsnamearg, factory),
              '__parameters__' : tuplize(key, clsnamearg, factory),
                  '__origin__' : metacls
        }
        
        # General question: should I do those two methods, “__str__”
        # and “__repr__”, with like __mro__ tricks or something, instead?
        
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
                     '__new__' : lambda cls, *args, **kw: factory(*args, **kw),
                 '__factory__' : staticmethod(factory)
            })
        
        # Create the new class, as one does in the override of a
        # metaclasses’ __new__(…) method, and stash it in a
        # metaclass-local dict keyed with the generated classname:
        
        baseset: list = kwargs.pop('baseset', [])
        
        cls = type(clsname, tuplize(key,
                                   *baseset,
                                    collections.abc.Iterable),
                            dict(attributes),
                          **kwargs)
        
        metacls.types[clsname] = metacls.TypeAndBases.for_type(cls)
        return cls
    
    @classmethod
    def __prepare__(metacls,
                       name: str,
                      bases: tx.Iterable[type],
                   **kwargs) -> tx.MutableMapping[str, tx.Any]:
        """ Maintain declaration order in class members: """
        return collections.OrderedDict()
    
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
        subbase: type = object
        for basecls in bases:
            if issubclass(basecls, (tx.Iterable,
                                    tx.Iterator)):
                subbase = basecls
                break
        
        # DON’T KNOW ABOUT YOU BUT I AM UN:
        debaser = tuplize(subbase,
                          collections.abc.Iterable,
                          collections.abc.Iterator)
        subname = kwargs.pop('subname', None)
        factory = kwargs.pop('factory', None)
        baseset = (len(bases) > 1) \
                   and [chien for chien in bases if chien not in debaser] \
                   or []
        
        # Create the base ancestor with a direct call to “__class_getitem__(…)”
        # -- which, note, will fail if no bases were specified; if `subbase`
        # defaults to “object”, this call will raise a TypeError, as it requires
        # an iterable operand:
        base = metacls.__class_getitem__(subbase,
                                         subname,
                                         factory,
                                         baseset=baseset,
                                       **kwargs)
        
        # The return value of type.__new__(…), called with the amended
        # inheritance-chain values, is what we pass off to Python:
        cls = super(OCDType, metacls).__new__(metacls, name,
                                                       tuplize(base),
                                                       dict(attributes),
                                                     **kwargs)
        
        metacls.subtypes[name] = metacls.TypeAndBases.for_type(cls)
        return cls

###
### SPECIALIZATIONS OF OCDType:
###

OCDSet        = OCDType[set]
OCDFrozenSet  = OCDType[frozenset, 'OCDFrozenSet']
OCDTuple      = OCDType[tuple]

class SortedList(list, metaclass=OCDType):
    pass

OCDList       = OCDType[list] # this emits the cached type from above

class Namespace(types.SimpleNamespace):
    
    def __bool__(self):
        return bool(self.__dict__)
    
    def __iter__(self):
        return iter(self.__dict__)
    
    def __len__(self):
        return len(self.__dict__)
    
    def __contains__(self, key):
        return key in self.__dict__

class SortedNamespace(Namespace, collections.abc.MutableMapping,
                                 collections.abc.Iterable,
                                 collections.abc.Sized,
                                 metaclass=OCDType):
    
    def __getitem__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        return super(SortedNamespace, self).__getitem__(key)
    
    def __setitem__(self, key, value):
        if not u8str(key).isidentifier():
            raise ValueError("key must be a valid identifier")
        super(SortedNamespace, self).__setattr__(key, value)

OCDNamespace  = OCDType[Namespace]


def test_namespace_types():
    """ Test instances of various SimpleNamespace subclasses """
    
    from pprint import pformat
    from utils import terminal_size
    
    nsdata: tx.Dict[str, str] = {
                'yo' : 'dogg',
                 'i' : 'heard',
               'you' : 'liked',
        'namespaced' : 'dictionary data'
    }
    
    simpleNamespace: types.SimpleNamespace = types.SimpleNamespace(**nsdata)
    namespace: Namespace = Namespace(**nsdata)
    ocdNamespace: OCDNamespace = OCDNamespace(**nsdata)
    sortedNamespace: SortedNamespace = SortedNamespace(**nsdata)
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
    
    from utils import print_cache
    from pprint import pprint
    
    """ 0. Set up some specializations and subtypes for testing: """
    
    import array
    OCDArray      = OCDType[array.array]
    
    import numpy
    OCDNumpyArray = OCDType[numpy.ndarray, 'OCDNumpyArray',
                            numpy.array]
    
    class SortedMatrix(numpy.matrix, metaclass=OCDType,
                                     subname='OCDMatrix',
                                     factory=numpy.asmatrix): pass
    
    ocd_settttts = OCDType[set]
    
    """ 1. Assert-check properties of specializations and subtypes: """
    
    assert ocd_settttts == OCDSet
    assert ocd_settttts.__name__ == 'OCDSet'
    assert ocd_settttts.__base__ == set
    assert not hasattr(ocd_settttts, '__factory__')
    assert ocd_settttts.__generic__ == tx.Set
    
    # pprint(dir(ocd_settttts))
    
    assert OCDSet[T]
    assert OCDSet[str]
    assert SortedMatrix[T]
    # print(type(OCDSet[T, S]))
    # pprint(type(OCDSet[S]))
    pprint(OCDSet[T])
    pprint(OCDNamespace[T, S])
    
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

if __name__ == '__main__':
    test()
