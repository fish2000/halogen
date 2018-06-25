
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

from rdom cimport RVar, RDom
from var cimport Var

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass VarOrRVar:
        
        VarOrRVar(string&, bint)
        VarOrRVar(Var&)
        VarOrRVar(RVar&)
        VarOrRVar(RDom&)
        
        string& name()
        
        Var var
        RVar rvar
        bint is_rvar

ctypedef vector[VarOrRVar] varorvec_t