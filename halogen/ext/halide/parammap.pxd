
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

from buffers cimport Buffer
from image cimport ImageParam
from param cimport Param
from parameter cimport Parameter
from runtime cimport halide_scalar_value_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass ParamMap:
        
        cppclass ParamMapping:
            
            Parameter* parameter
            ImageParam* image_param
            halide_scalar_value_t value
            Buffer[void] buf
            Buffer[void]* buf_out_param
            
            ParamMapping(ImageParam&, Buffer[void]&)
            ParamMapping(ImageParam&, Buffer[void]*)
        
        ParamMap()
        # ParamMap(initializer_list[ParamMapping]&) # NOT YET SUPPORTED
        
        void set[T](Param[T]&, T)
        void set(ImageParam&, Buffer[void]&)
        void set[T](ImageParam&, Buffer[T]&)
        
        size_t size()
        
        Parameter& map(Parameter&, Buffer[void]*&)
        
        @staticmethod
        ParamMap& empty_map()