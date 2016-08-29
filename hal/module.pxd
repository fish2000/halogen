
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from target cimport Target
from outputs cimport Outputs


cdef extern from "Halide.h" namespace "Halide::Internal::LoweredFunc":
    
    cdef enum LinkageType:
        External
        Internal

cdef extern from "Halide.h" namespace "Halide::Internal":
    
    cppclass LoweredFunc:
        string name
        LinkageType linkage

cdef extern from "Halide.h" namespace "Halide":
    
    cppclass Module:
        
        Module(string&, Target&)
        
        Target& target()
        string& name()
        void compile(Outputs&)

ctypedef vector[Module] modulevec_t

cdef extern from "Halide.h" namespace "Halide":

    Module link_modules(string&, modulevec_t&)
    void compile_standalone_runtime(string&, Target)            # creates object file
    Outputs compile_standalone_runtime(Outputs&, Target)        # creates object and/or static library
