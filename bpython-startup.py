#!/usr/bin/env python
from __future__ import print_function

import sys, os, re
import contextlib
import types
import typing as tx

from halogen import (api,
                     config,
                     compile,
                     compiledb,
                     filesystem,
                     ocd,
                     utils)

DISABLE_COLOR: bool = False
PrintFuncType = tx.Callable[[str, tx._TypingEllipsis], None]
TestFuncType = tx.Callable[[None], None]

class ColorForcer(contextlib.AbstractContextManager):
    
    """ Force-print using ANSI color codes, changing the relevant
        settings with context-managed safety
    """
    
    __slots__: tx.ClassVar[tx.Tuple[str, str]] = ('truthy', 'value')
    
    def __init__(self, *args, **kwargs):
        self.truthy: bool = True
        self.value: str = kwargs.pop('value', '1')
    
    def __enter__(self) -> "ColorForcer":
        global DISABLE_COLOR
        DISABLE_COLOR = False
        try:
            os.putenv('CLINT_FORCE_COLOR', self.value)
        except BaseException:
            self.truthy = False
        return self
    
    def __exit__(self, *args) -> bool:
        os.unsetenv('CLINT_FORCE_COLOR')
        return False
    
    def __bool__(self) -> bool:
        return self.truthy


def test(module: types.ModuleType, *, print_func: PrintFuncType = print) -> bool:
    """ Attempt to call `<module>.test()` – using a fallback function
        in the case that `<module>.test()` is not defined – in order
        to run that modules’ inline testsuite
    """
    modname: str = module.__name__
    print_func(f"TESTING MODULE: {modname}")
    fallback: TestFuncType = lambda: print_func(f"No inline test for module: {modname}\n")
    return_value: tx.Any = None
    try:
        return_value = getattr(module, 'test', fallback)()
    except BaseException as exc:
        print_func(f"*** Exception raised in {modname}.test():")
        print_func(exc)
    else:
        if return_value is not None:
            print_func(f"MODULE {modname} TEST RETURNED:")
            print_func(repr(return_value))
        return hasattr(module, 'test')
    return False

def testall(*, return_check_count=False) -> tx.Optional[int]:
    """ Attempt to call `<module>.test()` for all halogen modules,
        using the function call `test(<module>, print_function=printred)` –
        q.v. `test()` definition supra.
    """
    with ColorForcer() as color_forcer:
        try:
            from clint.textui import puts
            from clint.textui.colored import red
        except ImportError:
            def puts(*args):
                print(*args)
            def red(arg: tx.Any) -> tx.Any:
                return arg
        
        forcer_value: bool = bool(color_forcer)
        printred: PrintFuncType = forcer_value \
                                  and (lambda *args: puts(red(*args, always=True))) \
                                  or (lambda *args: print(*args))
        
        modules: tx.Tuple[types.ModuleType, ...] = (api,
                                                    config,
                                                    compile,
                                                    compiledb,
                                                    filesystem,
                                                    ocd,
                                                    utils)
        
        modcount: int = len(modules)
        checkcount: int = 0
        
        for module in modules:
            if test(module, print_func=printred):
                checkcount += 1
        
        printred(f"\nSuccessfully tested {checkcount} modules (of {modcount} total)")
        
        if return_check_count:
            return checkcount
        return None

if __name__ == '__main__':
    testall(return_check_count=True)
