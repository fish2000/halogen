
from libcpp.vector cimport vector
from intrusiveptr cimport IntrusivePtr

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass FunctionContents:
        pass


cdef extern from "Halide.h" namespace "Halide::ExternFuncArgument" nogil:
    
    cdef enum ArgType:
        UndefinedArg
        FuncArg
        BufferArg
        ExprArg
        ImageParamArg


ctypedef IntrusivePtr[FunctionContents] contents_ptr_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass ExternFuncArgument:
        
        ArgType arg_type
        
        # YO DOGG: need constructors for:
        # - Halide::Buffer
        # - Halide::Expr
        # x Internal::IntrusivePtr<Internal::FunctionContents>
        # - Internal::Parameter (== Halide::ImageParam)
        ExternFuncArgument(contents_ptr_t)
        ExternFuncArgument(int)
        ExternFuncArgument(float)
        ExternFuncArgument()
        
        bint is_func()
        bint is_expr()
        bint is_buffer()
        bint is_image_param()
        bint defined()

ctypedef vector[ExternFuncArgument] extargvec_t