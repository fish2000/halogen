
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

from argument cimport Argument
from buffer cimport Buffer
from expr cimport Expr
from function cimport ExternFuncArgument
from parameter cimport Parameter
from type cimport Type
from var cimport Var, varvec_t

ctypedef vector[Expr] exprvec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass OutputImageParam:
        
        OutputImageParam()
        
        string& name()
        Type type()
        bint defined()
        
        # Dimension dim(int)
        int dimensions()
        int host_alignment()
        OutputImageParam& set_host_alignment(int)
        
        Expr left()
        Expr right()
        Expr top()
        Expr bottom()
        Expr width()
        Expr height()
        Expr channels()
        
        Parameter parameter()
        # operator Argument()
        # operator ExternFuncArgument()
    
    cppclass Func
    
    cppclass ImageParam(OutputImageParam):
        
        ImageParam()
        ImageParam(Type, int)
        ImageParam(Type, int, string&)
        
        void set(Buffer[void])
        Buffer[void] get()
        void reset()
        
        Expr operator()(...)
        Expr operator()(exprvec_t)
        Expr operator()(varvec_t)
        
        # opeator Func()
        Func func_in "in"(Func&)
        Func func_in "in"(vector[Func]&)
        Func func_in "in"()
        
        bint is_explicit_name()
        void trace_loads()
        
        ImageParam& add_trace_tag(string&)
