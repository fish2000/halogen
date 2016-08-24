
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr

ctypedef vector[string] stringvec_t

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

cdef extern from "Halide.h" namespace "Halide::Internal":
    
    cppclass GeneratorBase(NamesInterface):
        pass
    
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


cdef extern from "Halide.h" namespace "Halide":
    
    cppclass Generator[T](GeneratorBase):
        Generator()
    
    cppclass RegisterGenerator[T]:
        RegisterGenerator(char*)
    
    
