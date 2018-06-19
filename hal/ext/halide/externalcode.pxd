
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

from device_api cimport DeviceAPI
from target cimport Target

ctypedef vector[uint8_t] bytevec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass ExternalCode:
        
        @staticmethod
        ExternalCode bitcode_wrapper(Target&, bytevec_t&, string&)
        
        @staticmethod
        ExternalCode device_code_wrapper(DeviceAPI, bytevec_t&, string&)
        
        @staticmethod
        ExternalCode c_plus_plus_code_wrapper(bytevec_t&, string&)
        
        bint is_for_cpu_target(Target&)
        bint is_for_device_api(DeviceAPI)
        bint is_c_plus_plus_source()
        
        bytevec_t& contents()
        string& name()