
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

# from expr cimport Expr

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Var:
        
        Var(string&)
        Var()
        
        string& name()
        bint same_as(Var&)
        
        @staticmethod
        Var implicit(int)
        
        @staticmethod
        bint is_implicit(string&)
        bint is_implicit()
        
        @staticmethod
        bint is_placeholder(string&)
        bint is_placeholder()
        
        # operator Expr()
        
        @staticmethod
        Var gpu_blocks()    # DEPRECIATED
        @staticmethod
        Var gpu_threads()   # DEPRECIATED
        
        @staticmethod
        Var outermost()

ctypedef vector[Var] varvec_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    varvec_t make_argument_list(int)