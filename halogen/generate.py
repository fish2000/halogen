# -*- coding: utf-8 -*-

from __future__ import print_function

valid_emits = frozenset([
    'assembly',
    'bitcode',
    'cpp', 'cpp_stub',
    'h', 'o',
    'static_library',
    'stmt',
    'stmt_html'
])

def preload(library_path, **kwargs):
    """ Load and auto-register generators from a dynamic-link library at a
        given path. Currently we use ctypes to do this cross-platform-ly.
        We also use a memoization cache to avoid loading anything twice.
    """
    import os, ctypes
    import config
    from errors import GeneratorError
    verbose = bool(kwargs.pop('verbose', config.DEFAULT_VERBOSITY))
    
    # initialize the memoization cache, if we haven’t already:
    if not hasattr(preload, 'loaded_libraries'):
        preload.loaded_libraries = {}
    
    # throw if the path is bad:
    if not os.path.exists(library_path):
        raise GeneratorError("No library exists at %s" % library_path)
    
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
    import os
    import config
    import hal.api
    from utils import terminal_width
    
    # ARGUMENT PROCESSING:
    
    generators = set([str(generator) for generator in generators])
    verbose = bool(arguments.pop('verbose', config.DEFAULT_VERBOSITY))
    target_string = bytes(arguments.pop('target', 'host'), encoding="UTF-8")
    generator_names = set(arguments.pop('generator_names', hal.api.registered_generators()))
    output_directory = os.path.abspath(arguments.pop('output_directory', os.path.relpath(os.getcwd())))
    emits = set(arguments.pop('emit', ['static_library', 'h']))
    substitutions = dict(arguments.pop('substitutions', dict()))
    
    # ARGUMENT POST-PROCESS BOUNDS-CHECKS:
    
    if target_string == b'':
        target_string = b"host"
    elif not hal.api.validate_target_string(target_string):
        raise ValueError("generation target string %s is invalid" % str(target_string))
    
    if len(generators) < 1:
        raise ValueError(">=1 generator is required")
    
    if len(generator_names) < 1:
        raise ValueError(">=1 generator name is required")
    
    if not generators.issubset(generator_names):
        # raise ValueError("unknown generator name in %s" % str(generators))
        raise ValueError("generator name in %s unknown to set: %s" % (str(generator_names - generators),
                                                                      str(generators)))
    
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    
    if not emits.issubset(valid_emits):
        raise ValueError("invalid emit in %s" % str(emits))
    
    if verbose:
        print("Compiling and running %s generators...\n" % len(generators))
    
    # Set up the default emit-options settings:
    emit_dict = dict(
        emit_static_library=False,
        emit_o=False, emit_h=False)
    
    # Set what emits to, er, emit, as per the “emit” keyword argument;
    # These have been rolled into the “emits” set (see argument processing, above);
    # …plus, we’ve already ensured that the set is valid:
    for emit in emits:
        emit_dict["emit_%s" % emit] = True
    
    # The “substitutions” keyword to the EmitOptions constructor is special;
    # It’s just a dict, passed forward during argument processing:
    emit_dict['substitutions'] = substitutions
    
    # Actually create the EmitOptions object from “emit_dict”:
    emit_options = hal.api.EmitOptions(**emit_dict)
    
    if verbose:
        print("Emit Options:")
        print(emit_options.to_string())
        print('')
    
    # The “target_string” variable defaults to “host” (see argument processing):
    target = hal.api.Target(target_string=target_string)
    
    if verbose:
        print("Target:")
        print(target.to_string())
        print('')
    
    # These lists will store generator module compilation artifacts:
    bsepths = list()
    outputs = list()
    modules = list()
    
    if verbose:
        print('-' * max(terminal_width, 160))
    
    # The generator loop compiles each named generator:
    for generator in generators:
        # “base_path” and “output” are computed using these API methods:
        base_path = hal.api.compute_base_path(output_directory, bytes(generator, encoding="UTF-8"), b"")
        output = emit_options.compute_outputs_for_target_and_path(target, base_path)
        
        # This next line was originally to compensate in a bug that only manifested
        # itself on my (now long-dead) MacBook Air:
        # output = outputs.static_library(None)
        
        if verbose:
            print("BSEPTH: %s" % str(base_path))
        
        if verbose:
            print("OUTPUT: %s" % output.to_string())
        
        # generator_args.update(arguments)
        
        if verbose:
            print("TARGET: %s" % target.to_string())
        
        # This API call prepares the generator code module:
        module = hal.api.get_generator_module(generator,
                                              arguments={ 'target': target.to_string() })
        
        if verbose:
            print("MODULE: %s" % module.to_string())
            print('-' * max(terminal_width, 160))
        
        # The compilation call:
        module.compile(output)
        
        # Stow the post-compile values:
        bsepths.append(base_path)
        outputs.append(output)
        modules.append(module)
    
    # Return the post-compile value lists for all generators:
    return bsepths, outputs, modules


def main():    
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    sys.path.append(os.path.dirname(__file__))
    
    # sys.path addenda necessary to load hal.api:
    import hal.api
    import config, tempfile
    
    assert str(hal.api.Target()) != 'host'
    
    print(hal.api.registered_generators())
    
    generate('my_first_generator',
        verbose=config.DEFAULT_VERBOSITY,
        target='host',
        output_directory=tempfile.gettempdir())
    
    generate('my_second_generator',
        verbose=config.DEFAULT_VERBOSITY,
        target='host',
        output_directory=tempfile.gettempdir())
    
    generate('brighten',
        verbose=config.DEFAULT_VERBOSITY,
        target='host',
        output_directory=tempfile.gettempdir())

if __name__ == '__main__':
    main()
