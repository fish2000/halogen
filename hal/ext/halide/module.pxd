
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from target cimport Target
from outputs cimport Outputs
from buffer cimport Buffer, buffervec_t

cdef extern from "Halide.h" namespace "Halide::Internal::LoweredFunc" nogil:
    
    cdef cppclass LinkageType:
        pass

cdef extern from "Halide.h" namespace "Halide::Internal::LoweredFunc::LinkageType" nogil:
    
    cdef LinkageType External
    cdef LinkageType Internal

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass LoweredFunc:
        string name
        LinkageType linkage

ctypedef vector[LoweredFunc] funcvec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Module:
        
        # Module()
        Module(string&, Target&)
        Module(Module&)
        
        Target& target()
        string& name()
        buffervec_t buffers()
        funcvec_t functions()
        void append(Buffer[void]&)
        void append(LoweredFunc&)
        LoweredFunc get_function_by_name(string&)
        void compile(Outputs&)

ctypedef vector[Module] modulevec_t

cdef extern from "Halide.h" namespace "Halide" nogil:

    Module link_modules(string&, modulevec_t&)
    void compile_standalone_runtime(string&, Target)            # creates object file
    Outputs compile_standalone_runtime(Outputs&, Target)        # creates object and/or static library
