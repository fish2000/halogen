
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

from expr cimport Expr
from intrusiveptr cimport RefCount, IntrusivePtr

ctypedef vector[Expr] exprvec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cdef cppclass Buffer[T]
    
cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass BufferContents:
        RefCount ref_count
        string name
    
    # Expr buffer_accessor(Buffer[void]&, exprvec_t&)
    
ctypedef IntrusivePtr[BufferContents] buffercontents_ptr_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cdef cppclass Buffer[T]:
        ctypedef T ElemType
        Buffer()
        # Buffer[T2](Buffer[T2]&)
        # Buffer[T2](Buffer[T2]&&)

ctypedef vector[Buffer[void]] buffervec_t