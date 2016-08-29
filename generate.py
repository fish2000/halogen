
valid_emits = frozenset([
    'assembly', 'bitcode',
    'cpp', 'h', 'html', 'o',
    'static_library',
    'stmt'
])

def generate(*generators, **arguments):
    import os
    import hal.api
    
    verbose = bool(arguments.pop('verbose', False))
    target_string = str(arguments.pop('target', 'host'))
    generators = set([str(generator) for generator in generators])
    generator_names = set(arguments.pop('generator_names',
                                        hal.api.registered_generators()))
    output_directory = os.path.abspath(arguments.pop('output_directory',
                                                     os.path.relpath(os.getcwd())))
    emits = set(arguments.pop('emit',
                             ['static_library', 'o', 'h']))
    extensions = arguments.pop('extensions', tuple())
    
    if target_string == '':
        raise ValueError("generation target unspecified")
    elif not hal.api.validate_target_string(target_string):
        raise ValueError("generation target %s is invalid" % target_string)
    
    if len(generators) < 1:
        raise ValueError(">=1 generator is required")
    
    if len(generator_names) < 1:
        raise ValueError(">=1 generator name is required")
    
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    
    if not emits.issubset(valid_emits):
        raise ValueError("invalid emit in %s" % str(emits))
    
    emit_dict = dict()
    emit_dict['emit_static_library'] = \
        emit_dict['emit_o'] = \
        emit_dict['emit_h'] = False
    emit_dict['extensions'] = dict(extensions)
    for emit in emits:
        emit_dict["emit_%s" % emit] = True
    
    emit_options = hal.api.EmitOptions(**emit_dict)
    target = hal.api.Target(target_string=target_string)
    
    for generator in generators:
        base_path = hal.api.compute_base_path(output_directory, generator, "")
        output_files = emit_options.compute_outputs_for_target_and_path(target, base_path)
