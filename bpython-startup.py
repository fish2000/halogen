#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import sys, os
import re
import contextlib
import types
import typing as tx
import typing_extensions as tX

if __package__ is None or __package__ == '':
    from halogen.utils import terminal_width
else:
    from .utils import terminal_width

DISABLE_COLOR: bool = False
PrintFuncType = tx.Callable[[str, tX._TypingEllipsis], None] # type: ignore
TestFuncType = tx.Callable[[None], None]
ExceptionType = tx.TypeVar('ExceptionType',
                            bound=BaseException,
                            covariant=True)

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
    
    def __exit__(self,
                 exc_type: tx.Optional[tx.Type[ExceptionType]] = None,
                 exc_val: tx.Optional[ExceptionType] = None,
                 exc_tb: tx.Optional[types.TracebackType] = None) -> bool:
        os.unsetenv('CLINT_FORCE_COLOR')
        return exc_type is not None
    
    def __bool__(self) -> bool:
        return self.truthy

def import_halogen_modules():
    from halogen import (api,
                         cli,
                         config,
                         compile,
                         compiledb,
                         errors,
                         filesystem,
                         generate,
                         ocd,
                         test_generators,
                         utils)
    assert api
    assert cli
    assert config
    assert compile
    assert compiledb
    assert errors
    assert filesystem
    assert generate
    assert ocd
    assert test_generators
    assert utils
    sys.modules.update({
        'halogen.api' : api,
        'halogen.cli' : cli,
        'halogen.config' : config,
        'halogen.compile' : compile,
        'halogen.compiledb' : compiledb,
        'halogen.errors' : errors,
        'halogen.filesystem' : filesystem,
        'halogen.generate' : generate,
        'halogen.ocd' : ocd,
        'halogen.test_generators' : test_generators,
        'halogen.utils' : utils
    })

def test_module(module: types.ModuleType, *, print_func: PrintFuncType = print) -> bool:
    """ Attempt to call `<module>.test()` – using a fallback function
        in the case that `<module>.test()` is not defined – in order
        to run that modules’ inline testsuite
    """
    modname: str = getattr(module, '__name__', "<unknown>")
    
    print_func('=' * terminal_width)
    print_func(f"TESTING MODULE: {modname}")
    print_func('-' * terminal_width)
    
    fallback: TestFuncType = lambda: print_func(f"No inline test for module: {modname}\n")
    return_value: tx.Any = None
    try:
        return_value = getattr(module, 'test', fallback)()
    except BaseException as exc:
        print_func(f"*** Exception raised in {modname}.test():")
        print_func(str(exc))
    else:
        if return_value is not None:
            print_func(f"MODULE {modname} TEST RETURNED:")
            print_func(repr(return_value))
        return hasattr(module, 'test')
    return False

def test_all(*, return_check_count: bool = False) -> tx.Optional[int]:
    """ Attempt to call `<module>.test()` for all halogen modules,
        using the function call `test(<module>, print_function=printred)` –
        q.v. `test()` definition supra.
    """
    import_halogen_modules()
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
                                                    cli,
                                                    config,
                                                    compile,
                                                    compiledb,
                                                    errors,
                                                    filesystem,
                                                    generate,
                                                    ocd,
                                                    test_generators,
                                                    utils)
        
        modcount: int = len(modules)
        checkcount: int = 0
        
        for module in modules:
            if test_module(module, print_func=printred):
                checkcount += 1
        
        printred(f"\nSuccessfully tested {checkcount} modules (of {modcount} total)")
        
        if return_check_count:
            return checkcount
        return None

if __name__ == '__main__':
    assert re # SHUT UP, PYFLAKES!!
    thispath: str = os.path.abspath(__file__)
    sys.path.append(os.path.dirname(os.path.join(thispath, 'halogen')))
    sys.path.append(os.path.dirname(thispath))
    import_halogen_modules()

from halogen import (api,
                     cli,
                     config,
                     compile,
                     compiledb,
                     errors,
                     filesystem,
                     generate,
                     ocd,
                     test_generators,
                     utils)

if __name__ == '__main__':
    test_all(return_check_count=True)