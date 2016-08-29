
from libc.stdint cimport *
from libcpp.map cimport map as std_map
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr
from target cimport Target
from type cimport Type
from module cimport Module, LinkageType

ctypedef vector[string]                 stringvec_t
ctypedef std_map[string, string]        stringmap_t

cdef extern from "Halide.h" namespace "Halide::Internal":
    
    cppclass GeneratorParamBase:
        string name
        GeneratorParamBase(string&)
        GeneratorParamBase(GeneratorParamBase&)


cdef extern from "Halide.h" namespace "Halide":
    
    cppclass GeneratorParam[T](GeneratorParamBase):
        GeneratorParam(string&, T&)
        void set(T&)
        void from_string(string&)
        string to_string()
    
    cppclass NamesInterface:
        pass


ctypedef GeneratorParam[Target]         targetparam_t

cdef extern from "Halide.h" namespace "Halide::Internal":
    
    ctypedef stringmap_t GeneratorParamValues
    
    cppclass GeneratorBase(NamesInterface):
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
            stringmap_t extensions
            EmitOptions()
        
        Target get_target()
        GeneratorParamValues get_generator_param_values()
        void set_generator_param_values(GeneratorParamValues&)
        int natural_vector_size(Type)
        # int natural_vector_size[T]()
        void emit_filter(string&, string&, string&, EmitOptions&)
        Module build_module(string&, LinkageType)
    
    cppclass GeneratorFactory:
        pass


ctypedef unique_ptr[GeneratorFactory]   factory_ptr_t
ctypedef unique_ptr[GeneratorBase]      base_ptr_t

cdef extern from "Halide.h" namespace "Halide::Internal":
    
    cppclass GeneratorRegistry:
        
        @staticmethod
        void register_factory(string& name, factory_ptr_t factory)
        
        @staticmethod
        void unregister_factory(string& name)
        
        @staticmethod
        stringvec_t enumerate()
        
        @staticmethod
        base_ptr_t create(string&, GeneratorParamValues&)


cdef extern from "Halide.h" namespace "Halide":
    
    cppclass Generator[T](GeneratorBase):
        Generator()
    
    cppclass RegisterGenerator[T]:
        RegisterGenerator(char*)


