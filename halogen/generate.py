# -*- coding: utf-8 -*-

from __future__ import print_function
from types import MappingProxyType as mappingproxy

valid_emits = frozenset((
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
emit_defaults = mappingproxy({ "emit_%s" % emit : False for emit in valid_emits })

# These are the default things to emit:
default_emits = ('static_library', 'h')

def preload(library_path, **kwargs):
    """ Load and auto-register generators from a dynamic-link library at a
        given path. Currently we use ctypes to do this cross-platform-ly.
        We also use a memoization cache to avoid loading anything twice.
    """
    import os, ctypes
    from config import DEFAULT_VERBOSITY
    from errors import GeneratorLoaderError
    verbose = bool(kwargs.pop('verbose', DEFAULT_VERBOSITY))
    
    # initialize the memoization cache, if we haven’t already:
    if not hasattr(preload, 'loaded_libraries'):
        preload.loaded_libraries = {}
    
    # throw if the path is bad:
    if not os.path.exists(library_path):
        raise GeneratorLoaderError("No library exists at %s" % library_path)
    
    # normalize the path:
    realpth = os.path.realpath(library_path)
    
    # return existant handle, because we already loaded that:
    if realpth in preload.loaded_libraries:
        if verbose:
            print("Library %s previously loaded" % realpth)
        return preload.loaded_libraries[realpth]
    
    # so far, I have no use for the object returned by LoadLibrary:
    preload.loaded_libraries[realpth] = ctypes.cdll.LoadLibrary(realpth)
    
    # return the new and freshly loaded handle
    if verbose:
        print("Library %s loaded afresh" % realpth)
    return preload.loaded_libraries[realpth]

def generate(*generators, **arguments):
    """ Invoke hal.api.Module.compile(…) with the proper arguments. This function
        was concieved with replacing GenGen.cpp’s options in mind. """
    import hal.api
    from config import DEFAULT_VERBOSITY
    from errors import GenerationError
    from filesystem import Directory
    from utils import terminal_width, u8bytes, u8str
    
    # ARGUMENT PROCESSING:
    
    generators = set(u8str(generator) for generator in generators)
    verbose = bool(arguments.pop('verbose', DEFAULT_VERBOSITY))
    target_string = u8bytes(arguments.pop('target', 'host'))
    generator_names = set(arguments.pop('generator_names', hal.api.registered_generators()))
    output_directory = Directory(arguments.pop('output_directory', None))
    emits = set(arguments.pop('emit', default_emits))
    substitutions = dict(arguments.pop('substitutions', {}))
    
    # ARGUMENT POST-PROCESS BOUNDS-CHECKS:
    
    if not target_string:
        target_string = b"host"
    elif not hal.api.validate_target_string(target_string):
        raise GenerationError("generation target string %s is invalid" % u8str(target_string))
    
    if len(generators) < 1:
        raise GenerationError(">=1 generator is required")
    
    if len(generator_names) < 1:
        raise GenerationError(">=1 generator name is required")
    
    if not generators.issubset(generator_names):
        # raise GenerationError("unknown generator name in %s" % str(generators))
        raise GenerationError("generator name in %s unknown to set: %s" % (str(generator_names),
                                                                           str(generators)))
    
    if not output_directory.exists:
        output_directory.makedirs()
    
    if not emits.issubset(valid_emits):
        raise GenerationError("invalid emit in %s" % str(emits))
    
    if verbose:
        print("Compiling and running %s generators...\n" % len(generators))
    
    # Set what emits to, er, emit, as per the “emit” keyword argument;
    # These have been rolled into the “emits” set (see argument processing, above);
    # …plus, we’ve already ensured that the set is valid:
    emit_dict = dict(emit_defaults)
    for emit in emits:
        emit_dict["emit_%s" % emit] = True
    
    # The “substitutions” keyword to the EmitOptions constructor is special;
    # It’s just a dict, passed forward during argument processing:
    emit_dict['substitutions'] = substitutions
    
    # Actually create the EmitOptions object from “emit_dict”:
    emit_options = hal.api.EmitOptions(**emit_dict)
    
    if verbose:
        print("Emit Options:")
        print(u8str(emit_options))
        print('')
    
    # The “target_string” variable defaults to “host” (see argument processing):
    target = hal.api.Target(target_string=target_string)
    
    if verbose:
        print("Target:")
        print(u8str(target))
        print('')
    
    # This list will store generator module compilation artifacts:
    artifacts = []
    
    if verbose:
        print('-' * max(terminal_width, 100))
    
    # The generator loop compiles each named generator:
    for generator in generators:
        # “base_path” (a bytestring) is computed using the `compute_base_path()` API function:
        base_path = hal.api.compute_base_path(u8bytes(output_directory.name),
                                              u8bytes(generator))
        
        # “output” (an hal.api.Outputs instance) is computed using the eponymously named
        # API function `compute_outputs_for_target_and_path()` with a hal.api.Target instance
        # and a base path (q.v. note supra):
        output = emit_options.compute_outputs_for_target_and_path(target, base_path)
        
        if verbose:
            print("BSEPTH: %s" % u8str(base_path))
            print("OUTPUT: %s" % u8str(output))
            print("TARGET: %s" % u8str(target))
        
        # generator_args.update(arguments)
        
        # This API call prepares the generator code module:
        module = hal.api.get_generator_module(generator,
                                              arguments={ 'target': str(target) })
        
        if verbose:
            print("MODULE: %s (%s)" % (u8str(module.name),
                                       u8str(module)))
            print('-' * max(terminal_width, 100))
        
        # The compilation call:
        module.compile(output)
        
        # Stow the post-compile values:
        artifacts.append((u8str(base_path), output, module))
    
    # Return the post-compile value artifacts for all generators:
    return artifacts


def main():
    
    """ Run the inline tests for the halogen.generate module """
    
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    sys.path.append(os.path.dirname(__file__))
    
    # sys.path addenda necessary to load hal.api:
    import hal.api
    import tempfile
    from config import DEFAULT_VERBOSITY
    
    assert str(hal.api.Target()) != 'host'
    
    print(hal.api.registered_generators())
    
    generate('my_first_generator',
        verbose=DEFAULT_VERBOSITY,
        target='host',
        output_directory=tempfile.gettempdir())
    
    generate('my_second_generator',
        verbose=DEFAULT_VERBOSITY,
        target='host',
        output_directory=tempfile.gettempdir())
    
    generate('brighten',
        verbose=DEFAULT_VERBOSITY,
        target='host',
        output_directory=tempfile.gettempdir())

if __name__ == '__main__':
    main()
