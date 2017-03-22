
from libc.stdint cimport *
from libcpp.map cimport map as std_map
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr

from target cimport Target
from type cimport Type
from module cimport Module, LinkageType

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass LoopLevel:
        # string func_name
        # string var_name
        # bint is_rvar
        # LoopLevel(string&, string&, bint)
        LoopLevel()


ctypedef vector[string]                 stringvec_t
ctypedef std_map[string, string]        stringmap_t
ctypedef std_map[string, LoopLevel]     llevelmap_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass GeneratorParamBase:
        string name
        GeneratorParamBase(string&)
        GeneratorParamBase(GeneratorParamBase&)

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass GeneratorContext:
        Target get_target()
    
    cppclass JITGeneratorContext:
        JITGeneratorContext(Target&)
        Target get_target()
    
    cppclass GeneratorParam[T](GeneratorParamBase):
        GeneratorParam(string&, T&)
        void set(T&)
        void from_string(string&)
        string to_string()
    
    cppclass NamesInterface:
        pass


ctypedef GeneratorParam[Target]         targetparam_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    ctypedef stringmap_t GeneratorParamValues
    
    cppclass GeneratorBase(NamesInterface, GeneratorContext):
        targetparam_t target
        
        cppclass EmitOptions:
            bint emit_o
            bint emit_h
            bint emit_cpp
            bint emit_assembly
            bint emit_bitcode
            bint emit_stmt
            bint emit_stmt_html
            bint emit_static_library
            bint emit_cpp_stub
            stringmap_t substitutions
            EmitOptions()
        
        Target get_target()
        
        void set_generator_param(string&, string&)
        void set_generator_param_values(stringmap_t&)
        
        GeneratorBase& set_generator_param[T](string&, T&)
        GeneratorBase& set_schedule_param[T](string&, T&)
        
        void set_schedule_param_values(stringmap_t&, llevelmap_t&)
        int natural_vector_size(Type)
        # int natural_vector_size[T]()
        
        void emit_cpp_stub(string&)
        # void emit_filter(string&, string&, string&, EmitOptions&)
        
        Module build_module(string&, LinkageType)
    
    cppclass GeneratorFactory:
        pass


ctypedef unique_ptr[GeneratorFactory]   factory_ptr_t
ctypedef unique_ptr[GeneratorBase]      base_ptr_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass GeneratorRegistry:
        
        @staticmethod
        void register_factory(string&, factory_ptr_t)
        
        @staticmethod
        void unregister_factory(string&)
        
        @staticmethod
        stringvec_t enumerate()
        
        @staticmethod
        base_ptr_t create(string&, JITGeneratorContext&, stringmap_t&)


cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Generator[T](GeneratorBase):
        Generator()
    
    cppclass RegisterGenerator[T]:
        RegisterGenerator(string&)

cdef inline base_ptr_t generator_registry_get(string& name,
                                              Target& target,
                                              stringmap_t& args):
    return GeneratorRegistry.create(name, JITGeneratorContext(target), args)

cdef inline base_ptr_t generator_registry_create(string& name):
    cdef Target t
    return GeneratorRegistry.create(name, JITGeneratorContext(t), stringmap_t())