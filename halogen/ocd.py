# -*- coding: utf-8 -*-

from __future__ import print_function

import abc
import collections
import collections.abc
import typing as tx

from utils import tuplize

__all__ = ('OCDType',
           'OCDSet', 'OCDFrozenSet',
           'OCDTuple', 'OCDList')

TypeFactory = tx.Callable[..., tx.Any]

class OCDType(abc.ABCMeta):
    
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
    
    # The metaclass-internal dictionaries of all generated types:
    types:    tx.Dict[str, type] = collections.OrderedDict()
    subtypes: tx.Dict[str, type] = collections.OrderedDict()
    
    class OCDMixin(object):
        
        """ A mixin for OCDType specializations to bequeath upon them the gift
            of being stringified.
        """
        
        token: str = ', '
        begin: str = '{ '
        endin: str = ' }'
        
        def __str__(self) -> str:
            return super().__str__()
        
        def __repr__(self) -> str:
            items = self.token.join(self.__iter__())
            return f"{self.begin}{items}{self.endin}"
    
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
        
        # If the class name already exists in the metaclass type dictionary,
        # return it without creating a new class:
        
        if clsname in metacls.types:
            return metacls.types[clsname]
        
        # Stow the covariant typevar and the computed name in the new class,
        # and install an `__iter__()` method that delegates to the covariant
        # implementation and wraps the results in a `sorted()` iterator before
        # returning them:
        it: tx.Iterable = tx.cast(tx.Iterable, key)
        
        attributes = {
             '__covariant__' : key,
                  '__name__' : clsname,
                  '__iter__' : lambda self: iter(sorted(it.__iter__(self))),
                  '__repr__' : metacls.OCDMixin.__repr__,
                   '__str__' : metacls.OCDMixin.__str__,
            
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
        
        cls = super(OCDType, metacls).__new__(metacls,
                                              clsname,
                                              tuplize(key,
                                                      collections.abc.Iterable,
                                                      metacls.OCDMixin),
                                              dict(attributes),
                                            **kwargs)
        metacls.types[clsname] = cls
        return cls
    
    @classmethod
    def __prepare__(metacls, name, bases, **kwargs) -> tx.Dict:
        """ Maintain declaration order in class members: """
        return collections.OrderedDict()
    
    def __new__(metacls, name, bases, attributes, **kwargs) -> type:
        """ When used as a metaclass, OCDType will insert a specialization
            of the class for which it has been chosen as a metaclass as its
            immediate base ancestor, and then create a new class based
            on that specialization for forwarding to Python’s class-creation
            apparatus:
        """
        subbase = object
        for basecls in bases:
            if issubclass(basecls, (tx.Iterable,
                                    tx.Iterator)):
                subbase = basecls
                break
        # others = tuplize(other for other in bases if other != subbase)
        subname = kwargs.pop('subname', None)
        factory = kwargs.pop('factory', None)
        
        # Create the base ancestor with a direct call to “__class_getitem__(…)”
        # -- which, note, will fail if no bases were specified; if `subbase`
        # defaults to “object”, this call will raise a TypeError, as it requires
        # an iterable operand:
        base = metacls.__class_getitem__(subbase,
                                         subname,
                                         factory,
                                       **kwargs)
        
        # The return value of type.__new__(…), called with the amended
        # inheritance-chain values, is what we pass off to Python:
        cls = super(OCDType, metacls).__new__(metacls, name,
                                                       tuplize(base),
                                                       dict(attributes),
                                                     **kwargs)
        metacls.subtypes[name] = cls
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


def test():
    """ Inline tests for OCDType and friends """
    
    from utils import print_cache
    
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
    
    assert OCDNumpyArray.__name__ == 'OCDNumpyArray'
    assert OCDNumpyArray.__base__ == numpy.ndarray
    assert OCDNumpyArray.__bases__ == tuplize(numpy.ndarray,
                                              collections.abc.Iterable,
                                              OCDType.OCDMixin)
    assert OCDNumpyArray.__factory__ == numpy.array
    
    assert SortedMatrix.__base__ == OCDType[numpy.matrix]
    assert SortedMatrix.__base__.__name__ == 'OCDMatrix'
    assert SortedMatrix.__base__.__base__ == numpy.matrixlib.defmatrix.matrix
    assert SortedMatrix.__base__.__factory__ == numpy.asmatrix
    
    assert OCDArray('i', range(10)).__len__() == 10
    assert numpy.array([[0, 1, 2], [0, 1, 2], [0, 1, 2]]).__len__() == 3
    assert OCDNumpyArray([[0, 1, 2], [0, 1, 2], [0, 1, 2]]).__len__() == 3
    assert SortedMatrix([[0, 1, 2], [0, 1, 2], [0, 1, 2]]).__len__() == 3
    assert SortedMatrix(OCDNumpyArray([[0, 1, 2], [0, 1, 2], [0, 1, 2]])).__len__() == 3
    
    """ 2. Reveal the cached OCDType specializations: """
    
    print_cache(OCDType, 'types')
    
    """ 3. Reveal the cached OCDType subtypes: """
    
    print_cache(OCDType, 'subtypes')

if __name__ == '__main__':
    test()
