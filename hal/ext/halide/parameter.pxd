
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

from buffers cimport Buffer
from expr cimport Expr
# from image cimport OutputImageParam
from runtime cimport halide_scalar_value_t, halide_buffer_t
from types cimport Type

ctypedef vector[Expr] exprvec_t
ctypedef Buffer[void] VoidBuffer

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass ParameterContents:
        pass
    
    cppclass Parameter:
        
        Parameter()
        Parameter(Type, bint, int)
        Parameter(Type, bint, int, string&, bint)
        Parameter(Parameter&)
        Parameter(Parameter&&)
        
        Parameter& operator=(Parameter&)
        Parameter& operator=(Parameter&&)
        
        Type type()
        int dimensions()
        string& name()
        bint is_explicit_name()
        bint is_buffer()
        
        T scalar[T]()
        Expr scalar_expr()
        void set_scalar[T](T)
        void set_scalar(Type&, halide_scalar_value_t)
        
        # Buffer[void] buffer()
        VoidBuffer buffer()
        halide_buffer_t* raw_buffer()
        # void set_buffer(Buffer[void])
        void set_buffer(VoidBuffer)
        void* scalar_address()
        
        bint same_as(Parameter&)
        bint defined()
        
        void set_min_constraint(int, Expr)
        void set_extent_constraint(int, Expr)
        void set_stride_constraint(int, Expr)
        void set_min_constraint_estimate(int, Expr)
        void set_extent_constraint_estimate(int, Expr);
        void set_host_alignment(int)
        Expr min_constraint(int)
        Expr extent_constraint(int)
        Expr stride_constraint(int)
        Expr min_constraint_estimate(int)
        Expr extent_constraint_estimate(int)
        int host_alignment()
        
        void set_min_value(Expr)
        Expr min_value()
        void set_max_value(Expr)
        Expr max_value()
        void set_estimate(Expr)
        Expr estimate()
        
        bint operator<(Parameter&)
    
    cppclass RegisteredParameter(Parameter):
        
        RegisteredParameter()
        RegisteredParameter(Type, bint, int, string&, bint)
        
        RegisteredParameter(Parameter&)
        RegisteredParameter& operator=(Parameter&)
        RegisteredParameter(RegisteredParameter&)
        RegisteredParameter& operator=(RegisteredParameter&)
        RegisteredParameter(RegisteredParameter&&)
        RegisteredParameter& operator=(RegisteredParameter&&)
    
    cdef void check_call_arg_types(string&, exprvec_t*, int)