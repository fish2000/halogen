
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr

from buffers cimport Buffer

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Realization:
        size_t size()
        Buffer[void]& operator[](size_t)
        Buffer[T] operator()[T]()
        Realization(vector[Buffer[void]]&)
        
        device_sync()
        device_sync(void*)