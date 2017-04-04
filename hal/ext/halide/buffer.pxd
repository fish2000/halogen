
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from intrusiveptr cimport IntrusivePtr

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass BufferContents:
        string name

ctypedef IntrusivePtr[BufferContents] buffercontents_ptr_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cdef cppclass Buffer[T]:
        Buffer()

ctypedef vector[Buffer[void]] buffervec_t