# -*- coding: utf-8 -*-

from __future__ import print_function

import typing as tx
from utils import tuplize

__all__ = ('OCDType',
           'OCDSet', 'OCDFrozenSet',
           'OCDTuple', 'OCDList')

TypeFactory = tx.Callable[..., tx.Any]

class OCDType(type):
    
    """ OCDType is a templated Python type.
    
        Literally, it is a subclass of `type`, allowing it to serve as a class
        factory, creating and customizing classes as do metaclasses. Unlike a
        typical Python metaclass, you directly engage with OCDType syntactically,
        to create your subclass specializations.
        
        It’s called OCDType because its primary reason for being is that it sorts
        its output iterators (at the time of writing, we use a vanilla call to the
        `sorted(…)` builtin, but I am sure that you, like me, can envision a whole
        shmörgasbord of doodads and geegaws that would allow for fine-tuning all
        those sort parameters.) It was written as a generalization of an extremely
        stupidly simple class called OCDSet, which extended the `set` builtin to
        intercept the output iterator and wrap it in a `sorted(…)`.
        
        But why use something dead-simple and functional, when you can spend a
        whole bunch more time generalizing the problem for no reason at all?
        Except for bragging rights maybe? In some mythical bar where many young,
        vivacious, attractive, scintillating Pythonistas of all imaginable genders
        congregate to regale one another of the various and sundry snippets of
        clever yet otherwise otioise code-morsels? This place does not exist,
        it is just you and me, and by you I mean this docstring and by me I mean
        me. Yes! Awesome. Anyway, as you were. Yes!
    """
    
    # The metaclass-internal name prefix, used to name generated
    # classes, á la Objective-C naming prefixes:
    prefix = "OCD"
    
    # The metaclass-internal dictionary of generated classes:
    types: tx.Dict[str, type] = {}
    
    class OCDMixin(object):
        
        """ A mixin for OCDType specializations to bequeath upon them the gift
            of being stringified.
        """
        
        token = ', '
        begin = '{ '
        endin = ' }'
        
        def __str__(self) -> str:
            return super().__str__()
        
        def __repr__(self) -> str:
            items = self.token.join(self.__iter__())
            return f"{self.begin}{items}{self.endin}"
    
    @classmethod
    def __class_getitem__(metacls, key: type,
                                   clsname: tx.Optional[str] = None,
                                   factory: tx.Optional[TypeFactory] = None) -> type:
        """ Specialize the templated type OCDType on a given iterable Python type.
            Returns the specialized OCDType.
        """
        from string import capwords
        
        # Validate covariant typevar argument:
        if not key:
            raise KeyError("OCDType is a templated type, "
                           "it requires a Python typevar on which to specialize")
        if type(key) == tuple:
            if len(key) == 2:
                key, clsname = key
            elif len(key) == 3:
                key, clsname, factory = key
        if type(key) != type:
            if not getattr(key, '__class__', None) == type:
                raise TypeError("OCDType is a templated type, "
                               f"it must be specialized using a Python typevar (not {type(key)})")
        if not hasattr(key, '__iter__'):
            raise TypeError("OCDType is a templated type, "
                            "it must be specialized on an iterable Python typevar")
        
        # Compute the name for the new class:
        if not clsname:
            name = capwords(key.__name__)
            clsname = f"{metacls.prefix}{name}"
        elif not clsname.startswith(metacls.prefix):
            clsname = f"{metacls.prefix}{clsname}"
        
        # If the class name already exists in the metaclass type dictionary,
        # return it without creating a new class:
        if clsname in metacls.types:
            return metacls.types[clsname]
        
        # Stow the covariant typevar and the computed name
        # in the new class, and install an `__iter__()` method
        # that delegates to the covariant implementation and
        # wraps the results in a `sorted()` iterator before
        # returning them:
        attributes = {
            '__covariant__'     :   key,
            '__name__'          :   clsname,
            '__iter__'          :   lambda self: iter(sorted(key.__iter__(self))),
            '__repr__'          :   metacls.OCDMixin.__repr__,
            '__str__'           :   metacls.OCDMixin.__str__,
            
            # q.v. inline notes to the Python 3 `typing` module
            # supra: https://git.io/fAsNO
            
            '__args__'          :   tuplize(key),
            '__parameters__'    :   tuplize(key),
            '__origin__'        :   metacls
        }
        
        # General question: should I do those last two methods with,
        # like, __mro__ tricks instead?
        
        if factory is not None:
            attributes.update({
                '__new__'       :   lambda cls, *args, **kwargs: factory(*args, **kwargs)
            })
        
        # Create the new class, as one does in the override of a
        # metaclasses’ __new__(…) method, and stash it in a
        # metaclass-local dict keyed with the generated classname:
        cls = super(OCDType, metacls).__new__(metacls, clsname,
                                                       tuplize(key, metacls.OCDMixin),
                                                       attributes,
                                                     **dict())
        metacls.types[clsname] = cls
        return cls
    
    @property
    @classmethod
    def typenames(metacls) -> tx.List[str]:
        return sorted(metacls.types.keys())
    
    @property
    @classmethod
    def typecachesize(metacls) -> int:
        return len(metacls.types)

###
### SPECIALIZATIONS OF OCDType:
###

OCDSet        = OCDType[set]
OCDFrozenSet  = OCDType[frozenset, 'OCDFrozenSet']
OCDTuple      = OCDType[tuple]
OCDList       = OCDType[list]


def test():
    from utils import print_cache
    
    import array
    OCDArray      = OCDType[array.array]
    
    import numpy
    OCDNumpyArray = OCDType[numpy.ndarray, 'OCDNumpyArray',
                            numpy.array]
    
    ocd_settttts = OCDType[set]
    assert ocd_settttts == OCDSet
    
    assert OCDArray('i', range(10)).__len__()
    assert numpy.array([[0, 1, 2], [0, 1, 2], [0, 1, 2]]).__len__()
    assert OCDNumpyArray([[0, 1, 2], [0, 1, 2], [0, 1, 2]]).__len__()
    
    """ 1. Reveal the cached OCDType specializations: """
    
    print_cache(OCDType, 'types')

if __name__ == '__main__':
    test()
