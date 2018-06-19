
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

from expr cimport Expr
from function cimport Function, functionvec_t
from target cimport Target

ctypedef vector[uint8_t] bytevec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass MachineParams:
        
        Expr parallelism
        Expr last_level_cache_size
        Expr balance
        
        @staticmethod
        MachineParams generic()
        
        MachineParams(int32_t, int32_t, int32_t)
        MachineParams(string&)
        
        string to_string()

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    string generate_schedules(functionvec_t&, Target&, MachineParams&)