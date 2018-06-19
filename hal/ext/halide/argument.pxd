
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr

from buffer cimport Buffer
from expr cimport Expr
from type cimport Type

cdef extern from "Halide.h" namespace "Halide::Argument" nogil:

    cdef cppclass Kind:
        pass

cdef extern from "Halide.h" namespace "Halide::Argument::Kind" nogil:

    cdef Kind InputScalar
    cdef Kind InputBuffer
    cdef Kind OutputBuffer

cdef extern from "Halide.h" namespace "Halide" nogil:

    cppclass Argument:
        string name
        Kind kind
        uint8_t dimensions
        Type argument_type "type"
        Expr argument_def  "def"
        Expr argument_min  "min"
        Expr argument_max  "max"
        
        Argument()
        Argument(string&, Kind, Type&, int)
        # Argument(Buffer[])
        
        bint is_buffer()
        bint is_scalar()
        bint is_input()
        bint is_output()
        
        bint operator==(Argument&)