
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

from expr cimport Expr
from type cimport Type

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Param[T]:
        
        ctypedef T not_void_T
        
        @staticmethod
        Type static_type()
        
        Param()
        Param(Type)
        Param(string&)
        Param(char*)
        Param(Type, string&)
        
        Param(string&, not_void_T)
        Param(not_void_T, Expr, Expr) # min, max
        Param(string&, not_void_T, Expr, Expr) # min, max
        
        string& name()
        bint is_explicit_name()
        
        T2 get[T2]()
        void set[SOME_TYPE](SOME_TYPE&)
        
        Type type()
        void set_range(Expr, Expr) # min, max
        void set_min_value(Expr)
        void set_max_value(Expr)
        Expr min_value()
        Expr max_value()
        
        void set_estimate[SOME_TYPE](SOME_TYPE&)
        
        # operator Expr()
        # operator ExternFuncArgument()
        # operator Argument()
        # Parameter parameter()
    
    cdef Expr user_context_value()