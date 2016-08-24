# distutils: language = c++

from target cimport Target as HalTarget
from target cimport get_host_target as halide_get_host_target
from target cimport get_target_from_environment as halide_get_target_from_environment
from target cimport get_jit_target_from_environment as halide_get_jit_target_from_environment


## CLASS WRAPPER:

cdef class Target:
    """ Cython wrapper class for Halide::Target """
    
    cdef:
        HalTarget __this__
    
    def __cinit__(Target self, *args, **kwargs):
        # if '__this__' in kwargs:
        #     self.__this__ = <HalTarget>kwargs.get('__this__')
        pass
        
    
    def __init__(Target self, *args, **kwargs):
        # if target_string is not None:
        #     self.__this__ = HalTarget(target_string)
        if 'target_string' in kwargs:
            self.__this__ = HalTarget(kwargs.get('target_string'))
    
    def __dealloc__(Target self):
        pass
    
    cdef int is_it_live(Target self) except -1:
        # if self.__this__ == NULL:
        #     raise RuntimeError("HalTarget is NULL")
        # else:
        #     return 0
        return 0
    
    property os:
        
        def __get__(Target self):
            self.is_it_live()
            return self.__this__.os
            
        def __set__(Target self, value):
            self.is_it_live()
            self.__this__.bits = <HalTarget.OS>value
    
    property arch:
        
        def __get__(Target self):
            self.is_it_live()
            return self.__this__.arch
    
        def __set__(Target self, value):
            self.is_it_live()
            self.__this__.bits = <HalTarget.Arch>value
    
    property bits:
        
        def __get__(Target self):
            self.is_it_live()
            return self.__this__.bits
        
        def __set__(Target self, value):
            self.is_it_live()
            self.__this__.bits = <int>value
    
    def has_gpu_feature(Target self):
        self.is_it_live()
        return self.__this__.has_gpu_feature()
    
    def to_string(Target self):
        self.is_it_live()
        return self.__this__.to_string()
    
    def maximum_buffer_size(Target self):
        self.is_it_live()
        return self.__this__.maximum_buffer_size()
    
    def supported(Target self):
        self.is_it_live()
        return self.__this__.supported()
    
    def __str__(Target self):
        self.is_it_live()
        return self.__this__.to_string()
    
    def __enter__(Target self):
        self.is_it_live()
        return self
    
    def __exit__(Target self, exc_tp, exc_val, exc_tb):
        # if self.__this__ != NULL:
        #     del self.__this__
        #     self.__this__ = NULL
        # return False
        return False
    


## FUNCTION WRAPPERS:
def get_host_target():
    out = Target()
    out.__this__ = halide_get_host_target()
    return out

def get_target_from_environment():
    out = Target()
    out.__this__ = halide_get_target_from_environment()
    return out

def get_jit_target_from_environment():
    out = Target()
    out.__this__ = halide_get_jit_target_from_environment()
    return out

def validate_target_string(target_string):
    return HalTarget.validate_target_string(target_string)

