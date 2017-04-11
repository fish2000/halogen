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
    
    generators = set([str(generator) for generator in generators])
    verbose = bool(arguments.pop('verbose', config.DEFAULT_VERBOSITY))
    target_string = str(arguments.pop('target', 'host'))
    generator_names = set(arguments.pop('generator_names', hal.api.registered_generators()))
    output_directory = os.path.abspath(arguments.pop('output_directory', os.path.relpath(os.getcwd())))
    emits = set(arguments.pop('emit', ['static_library', 'h']))
    substitutions = dict(arguments.pop('substitutions', dict()))
    
    if target_string == '':
        target_string = "host"
    elif not hal.api.validate_target_string(target_string):
        raise ValueError("generation target string %s is invalid" % target_string)
    
    if len(generators) < 1:
        raise ValueError(">=1 generator is required")
    
    if len(generator_names) < 1:
        raise ValueError(">=1 generator name is required")
    
    if not generators.issubset(generator_names):
        raise ValueError("unknown generator name in %s" % str(generators))
    
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    
    if not emits.issubset(valid_emits):
        raise ValueError("invalid emit in %s" % str(emits))
    
    if verbose:
        print("Compiling and running %s generators..." % len(generators))
        print('')
    
    emit_dict = dict(
        emit_static_library=False,
        emit_o=False, emit_h=False)
    
    # emit_dict['emit_static_library'] = \
    #     emit_dict['emit_o'] = \
    #     emit_dict['emit_h'] = False
    
    for emit in emits:
        emit_dict["emit_%s" % emit] = True
    emit_dict['substitutions'] = substitutions
    
    emit_options = hal.api.EmitOptions(**emit_dict)
    
    if verbose:
        print("Emit Options:")
        print(emit_options.to_string())
        print('')
    
    target = hal.api.Target(target_string=target_string)
    
    if verbose:
        print("Target:")
        print(target.to_string())
        print('')
    
    bsepths = list()
    outputs = list()
    modules = list()
    
    if verbose:
        print('-' * max(terminal_width, 160))
    
    for generator in generators:
        base_path = hal.api.compute_base_path(output_directory, generator, "")
        output = emit_options.compute_outputs_for_target_and_path(target, base_path)
        
        # This next line was originally to compensate in a bug that only manifested
        # itself on my (now long-dead) MacBook Air:
        # output = outputs.static_library(None)
        
        if verbose:
            print("BSEPTH: %s" % str(base_path))
        
        if verbose:
            print("OUTPUT: %s" % output.to_string())
        
        generator_args = dict(target=target.to_string())
        # generator_args.update(arguments)
        
        if verbose:
            print("TARGET: %s" % target.to_string())
            # print('')
        
        module = hal.api.get_generator_module(generator, arguments=generator_args)
        
        if verbose:
            print("MODULE: %s" % module.to_string())
            print('-' * max(terminal_width, 160))
        
        module.compile(output)
        
        bsepths.append(base_path)
        outputs.append(output)
        modules.append(module)
    
    return bsepths, outputs, modules


def main():
    import config
    
    generate('my_first_generator',
        verbose=config.DEFAULT_VERBOSITY,
        target='host',
        output_directory='/tmp')
    
    generate('my_second_generator',
        verbose=config.DEFAULT_VERBOSITY,
        target='host',
        output_directory='/tmp')
    
    generate('brighten',
        verbose=config.DEFAULT_VERBOSITY,
        target='host',
        output_directory='/tmp')

if __name__ == '__main__':
    main()
