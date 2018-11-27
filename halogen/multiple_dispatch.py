#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# multiple_dispatch.py
# 
# My version:
# https://gist.github.com/fish2000/1af4b852d20b7568a9b9c90fe2346b6d
#
# Forked from the originall by @wolfv:
# https://gist.github.com/wolfv/73f56e4a9cac84eea6a796fde3213456
#
# * See below for usage notes

import typing as tx
import re
import types
import collections.abc

__all__ = ('overloaded', 'T', 'U')
__dir__ = lambda: list(__all__)

VERBOSE = True

def nameof(arg):
    return arg.__name__

def typename(arg):
    return nameof(type(arg))

def origin(arg, default_type=object):
    return getattr(arg, '__origin__', default_type)

def is_generic_sequence(arg):
    return origin(arg) is collections.abc.Sequence

def is_generic_iterable(arg):
    return origin(arg) is collections.abc.Iterable

def can_be_iterated(arg):
    return is_generic_sequence(arg) or is_generic_iterable(arg)

def to_matchgroup(arg, groups):
    if type(arg) is tx.TypeVar:
        if arg in groups:
            return "(?P={})".format(nameof(arg))
        else:
            groups |= { arg }
            return "(?P<{}>.*?)".format(nameof(arg))
    else:
        return to_regex(arg, groups)

def to_regex(typevar, groups):
    if typevar in { float, int, str, bytes }:
        return nameof(typevar)
    elif is_generic_sequence(typevar):
        return "(?:list|tuple)\[{}\]".format(to_matchgroup(typevar.__args__[0], groups))
    elif is_generic_iterable(typevar):
        return "(?:set|frozenset|generator)\[{}\]".format(to_matchgroup(typevar.__args__[0], groups))
    return ".*?"

def get_element_types(sequence):
    out = []
    if sequence is None:
        return out
    typeset = { type(el) for el in sequence }
    for el in sequence:
        eltype = type(el)
        if eltype in typeset and eltype not in out:
            out.append(eltype)
    return out

def to_callee(arg, argtype):
    if argtype in { float, int, str, bytes }:
        return nameof(argtype)
    elif argtype in { list, tuple, set, frozenset }:
        t = nameof(argtype) + '[{}]'
        eltypes = get_element_types(arg)
        if len(eltypes) == 0:
            return t.format('')
        if len(eltypes) == 1:
            return t.format(nameof(eltypes[0]))
        else:
            raise RuntimeError(">1 type subscript not implemented yet.")
    elif argtype in { types.GeneratorType,
                      types.AsyncGeneratorType }:
        return nameof(argtype) + '[Any]'
    else:
        raise RuntimeError(f"Argument encoding for {nameof(argtype)} not implemented yet.")

def to_match_target(caller_signature):
    return ", ".join(to_callee(el, type(el)) for el in caller_signature)

def to_callee_string(caller_signature):
    elements = []
    for sigtype in caller_signature:
        origtype = origin(sigtype, sigtype)
        try:
            elements.append((origtype(), origtype))
        except TypeError:
            elements.append((origtype.__args__[0], origtype))
    return ", ".join(to_callee(*element) for element in elements)

def to_regex_sig(caller_signature):
    groups = set()
    return ", ".join(to_regex(el, groups) for el in caller_signature)

class overloaded(object):

    fmap = {}

    def __init__(self, f):
        signature = tuple(x[1] for x in f.__annotations__.items())
        self.fmap[to_regex_sig(signature)] = f

    def __call__(self, *args):
        match_sig = to_match_target(args)
        for key, func in self.fmap.items():
            if VERBOSE:
                print("Matching: {} against\n          {}\n".format(match_sig, key))
            if (re.match(key, match_sig)):
                if VERBOSE:
                    print("          === MATCH ===\n\n")
                return func(*args)
        else:
            raise RuntimeError("No overload found for ", match_sig)

    def __getitem__(self, params):
        if not hasattr(params, '__iter__') or type(params) is type:
            params = tuple([params])
        else:
            params = tuple(item for item in params if item is not None)
        match_sig = to_callee_string(params)
        for key, func in self.fmap.items():
            if VERBOSE:
                print("Matching: {} against\n          {}\n".format(match_sig, key))
            if (re.match(key, match_sig)):
                if VERBOSE:
                    print("          === MATCH ===\n\n")
                return func
        raise RuntimeError("No overload found for ", match_sig)

@overloaded
def add(a: int, b: int):
    return a + b + 100

@overloaded
def add(a: float, b: float):
    return a + b

T = tx.TypeVar('T')
U = tx.TypeVar('U')

@overloaded
def add(a: tx.Sequence[T], b: float):
    return [x + b for x in a]

@overloaded
def add(a: tx.Sequence[T], b: tx.Sequence[str]):
    return [str(x) + y for x, y in zip(a, b)]

@overloaded
def add(a: tx.Sequence[T], b: tx.Sequence[U]):
    return [x + y for x, y in zip(a, b)]

@overloaded
def add(a: tx.Sequence[T], b: tx.Iterable[U]):
    return add(a, list(b))

@overloaded
def add(a: tx.Sequence[T], b: tx.Iterable[str]):
    return add(a, b)

def main():
    print(add(3, 5))
    print()
    
    print(add(4.5, 8.2))
    print()
    
    print(add([1, 2, 3], 5.0))
    print()
    
    print(add([1, 2, 3], [1, 2, 3]))
    print()
    
    print(add([1, 2, 3], ["a", "b", "c"]))
    print()
    
    print(add([1, 2, 3], { "a", "b", "c" }))
    print()
    
    print(add([1, 2, 3], (x.upper() for x in ["a", "b", "c"])))
    print()
    
    print(add[list, list])
    print(add[tx.List, tx.List[str]])

if __name__ == '__main__':
    main()