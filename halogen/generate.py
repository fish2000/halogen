#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from types import MappingProxyType as mappingproxy
import typing as tx

if __package__ is None or __package__ == '':
    from ocd import OCDFrozenSet
else:
    from .ocd import OCDFrozenSet

__all__ = ('valid_emits', 'emit_defaults',
                          'default_emits',
           'preload',
           'generate')

__dir__ = lambda: list(__all__)

valid_emits: tx.FrozenSet[str] = OCDFrozenSet((
    'assembly',
    'bitcode',
    'cpp', 'cpp_stub',
    'h', 'o',
    'python_extension',
    'static_library',
    'stmt',
    'stmt_html',
    'schedule'
))

# Set the default emit options to False for all:
emit_defaults = mappingproxy({ f"emit_{emit}" : False for emit in valid_emits })

# These are the default things to emit:
default_emits = ('static_library', 'h')

def preload(library_path, **kwargs):
    """ Load and auto-register generators from a dynamic-link library at a
        given path. Currently we use ctypes to do this cross-platform-ly.
        We also use a memoization cache to avoid loading anything twice.
    """
    import os, ctypes
    if __package__ is None or __package__ == '':
        from config import DEFAULT_VERBOSITY
        from errors import GeneratorLoaderError
    else:
        from .config import DEFAULT_VERBOSITY
        from .errors import GeneratorLoaderError
    verbose = bool(kwargs.pop('verbose', DEFAULT_VERBOSITY))
    
    # initialize the memoization cache, if we haven’t already:
    if not hasattr(preload, 'loaded_libraries'):
        preload.loaded_libraries = {}
    
    # throw if the path is bad:
    if not os.path.exists(library_path):
        raise GeneratorLoaderError(f"preload(): No library exists at {library_path}")
    
    # normalize the path:
    realpth = os.path.realpath(library_path)
    
    # return existant handle, because we already loaded that:
    if realpth in preload.loaded_libraries:
        if verbose:
            print(f"preload(): Library {realpth} previously loaded")
        return preload.loaded_libraries[realpth]
    
    # so far, I have no use for the object returned by LoadLibrary:
    preload.loaded_libraries[realpth] = ctypes.cdll.LoadLibrary(realpth)
    
    # return the new and freshly loaded handle
    if verbose:
        print(f"preload(): Library {realpth} loaded afresh")
    return preload.loaded_libraries[realpth]

def generate(*generators, **arguments):
    """ Invoke halogen.api.Module.compile(…) with the proper arguments. This function
        was concieved with replacing GenGen.cpp’s options in mind. """
    import os
    if __package__ is None or __package__ == '':
        import api # type: ignore
        from config import DEFAULT_VERBOSITY
        from errors import GenerationError
        from filesystem import Directory
        from utils import terminal_width, u8bytes, u8str
    else:
        from . import api # type: ignore
        from .config import DEFAULT_VERBOSITY
        from .errors import GenerationError
        from .filesystem import Directory
        from .utils import terminal_width, u8bytes, u8str
    
    # ARGUMENT PROCESSING:
    
    generators = { u8str(generator) for generator in generators }
    generator_names = OCDFrozenSet(arguments.pop('generator_names', api.registered_generators()))
    output_directory = Directory(pth=arguments.pop('output_directory', None))
    target = api.Target(target_string=u8bytes(arguments.pop('target', 'host')))
    emits = OCDFrozenSet(arguments.pop('emit', default_emits))
    substitutions = dict(arguments.pop('substitutions', {}))
    verbose = bool(arguments.pop('verbose', DEFAULT_VERBOSITY))
    
    # ARGUMENT POST-PROCESS BOUNDS-CHECKS:
    
    if len(generators) == 0:
        raise GenerationError(">=1 generator is required")
    
    if len(generator_names) == 0:
        raise GenerationError(">=1 generator name is required")
    
    if not generators.issubset(generator_names):
        raise GenerationError(f"generator name in {str(generator_names)} unknown to set: {str(generators)}")
    
    if not output_directory.exists:
        output_directory.makedirs()
    
    if not emits.issubset(valid_emits):
        raise GenerationError(f"invalid emit in {str(emits)}")
    
    if verbose:
        print("")
        print(f"generate(): Preparing {len(generators)} generator modules to emit data …")
        print("")
    
    # Set what emits to, er, emit, as per the “emit” keyword argument;
    # These have been rolled into the “emits” set (q.v. argument processing supra.);
    # …plus, we’ve already ensured that the set is valid:
    emit_dict = dict(emit_defaults)
    for emit in emits:
        emit_dict[f"emit_{emit}"] = True
    
    # The “substitutions” keyword to the EmitOptions constructor is special;
    # It’s just a dict, passed forward during argument processing:
    emit_dict['substitutions'] = substitutions
    
    # Actually create the EmitOptions object from “emit_dict”:
    emit_options = api.EmitOptions(**emit_dict)
    
    if verbose:
        print(f"generate(): Target: {u8str(target)}")
        print("generate(): Emit Options:")
        print(u8str(emit_options))
        print("")
    
    # This list will store generator module compilation artifacts:
    artifacts = []
    
    if verbose:
        print('-' * max(terminal_width, 100))
    
    # The generator loop compiles each named generator:
    for generator in generators:
        
        # “base_path” (a bytestring) is computed using the `compute_base_path()` API function:
        base_path = api.compute_base_path(u8bytes(
                                        os.fspath(output_directory)),
                                          u8bytes(generator))
        
        # “output” (an instance of halogen.api.Outputs) is computed using the eponymously named
        # halogen.api.EmitOptions method `compute_outputs_for_target_and_path()` with an instance
        # of halogen.api.Target and a base path bytestring (q.v. note supra.):
        output = emit_options.compute_outputs_for_target_and_path(target, base_path)
        
        if verbose:
            print(f"BSEPTH: {u8str(base_path)}")
            print(f"OUTPUT: {u8str(output)}")
        
        # This API call prepares the generator code module:
        module = api.get_generator_module(generator,
                                          arguments={ 'target': target })
        
        if verbose:
            print(f"MODULE: {u8str(module.name)} ({u8str(module)})")
            print('=' * max(terminal_width, 100))
        
        # The module-compilation call:
        module.compile(output)
        
        # Stow the post-compile base path (a string), outputs (an instance of
        # halogen.api.Outputs) and the module instance itself:
        artifacts.append((u8str(base_path), output, module))
    
    # Return the post-compile value artifacts for all generators:
    return artifacts


def test():
    
    """ Run the inline tests for the halogen.generate module """
    
    import os
    if __package__ is None or __package__ == '':
        import api # type: ignore
        from filesystem import TemporaryDirectory
        from utils import tuplize
    else:
        from . import api # type: ignore
        from .filesystem import TemporaryDirectory
        from .utils import tuplize
    
    assert str(api.Target()) != 'host'
    registered_generators = api.registered_generators()
    
    if len(registered_generators) > 0:
        print(registered_generators)
        print()
        
        with TemporaryDirectory(prefix='yo-dogg-') as td:
            
            generate(*tuplize('my_first_generator'),
                target='host',
                output_directory=os.fspath(td))
            
            generate(*tuplize('my_second_generator'),
                target='host',
                output_directory=os.fspath(td))
            
            generate(*tuplize('my_brightest_generator'),
                target='host',
                output_directory=os.fspath(td))
    else:
        print("No registered generators found, skipping inline tests")
        # print()

if __name__ == '__main__':
    test()
