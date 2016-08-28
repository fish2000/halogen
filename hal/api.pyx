# distutils: language = c++

from libc.stdint cimport *
from libcpp.string cimport string
# from libcpp.vector cimport vector

from generator cimport GeneratorRegistry, Generator, RegisterGenerator

from type cimport Type as HalType
from type cimport Int as Type_Int
from type cimport UInt as Type_UInt
from type cimport Float as Type_Float
from type cimport Bool as Type_Bool
from type cimport Handle as Type_Handle

from target cimport Target as HalTarget
from target cimport get_host_target as halide_get_host_target
from target cimport get_target_from_environment as halide_get_target_from_environment
from target cimport get_jit_target_from_environment as halide_get_jit_target_from_environment


def registered_generators():
    return tuple(GeneratorRegistry.enumerate())


cdef class Type:
    """ Cython wrapper class for Halide::Type """
    
    cdef:
        HalType __this__
    
    @staticmethod
    def fromother(Type other):
        out = Type()
        out.__this__ = HalType(other.__this__)
        return out
    
    def __cinit__(Type self, Type other=None, **kwargs):
        if other is not None:
            self.__this__ = HalType(other.__this__)
    
    def __init__(Type self, *args, **kwargs):
        if len(args) < 1:
            if 'code' in kwargs:
                self.__this__ = self.__this__.with_code(kwargs.get('code'))
            elif 'bits' in kwargs:
                self.__this__ = self.__this__.with_bits(<uint8_t>kwargs.get('bits'))
            elif 'lanes' in kwargs:
                self.__this__ = self.__this__.with_lanes(<uint16_t>kwargs.get('lanes'))
    
    def code(Type self):
        return self.__this__.code()
    
    def bytes(Type self):
        return self.__this__.bytes()
    
    def bits(Type self):
        return self.__this__.bits()
    
    def lanes(Type self):
        return self.__this__.lanes()
    
    def with_code(Type self, code):
        out = Type()
        out.__this__ = self.__this__.with_code(code)
        return out
    
    def with_bits(Type self, bits):
        out = Type()
        out.__this__ = self.__this__.with_bits(<uint8_t>bits)
        return out
    
    def with_lanes(Type self, lanes):
        out = Type()
        out.__this__ = self.__this__.with_lanes(<uint16_t>lanes)
        return out
    
    def is_bool(Type self):
        return self.__this__.is_bool()
    
    def is_vector(Type self):
        return self.__this__.is_vector()
    
    def is_scalar(Type self):
        return self.__this__.is_scalar()
    
    def is_float(Type self):
        return self.__this__.is_float()
    
    def is_int(Type self):
        return self.__this__.is_int()
    
    def is_uint(Type self):
        return self.__this__.is_uint()
    
    def is_handle(Type self):
        return self.__this__.is_handle()
    
    def same_handle_type(Type self, Type other):
        return self.__this__.same_handle_type(other.__this__)
    
    def element_of(Type self):
        out = Type()
        out.__this__ = self.__this__.element_of()
        return out
    
    def can_represent(Type self, other):
        if type(other) == type(self):
            return self.can_represent_type(other)
        elif type(other) == type(float()):
            return self.can_represent_float(float(other))
        elif type(other) == type(int()) or \
             type(other) == type(long()):
            return self.can_represent_long(long(other))
        return False
    
    def can_represent_type(Type self, Type other):
        return self.__this__.can_represent(other.__this__)
    
    def can_represent_float(Type self, float other):
        return self.__this__.can_represent(<double>other)
    
    def can_represent_long(Type self, long other):
        return self.__this__.can_represent(<int64_t>other)
    
    @staticmethod
    def Int(int bits, int lanes=1):
        out = Type()
        out.__this__ = Type_Int(bits, lanes)
        return out
    
    @staticmethod
    def UInt(int bits, int lanes=1):
        out = Type()
        out.__this__ = Type_UInt(bits, lanes)
        return out
    
    @staticmethod
    def Float(int bits, int lanes=1):
        out = Type()
        out.__this__ = Type_Float(bits, lanes)
        return out
    
    @staticmethod
    def Bool(int lanes=1):
        out = Type()
        out.__this__ = Type_Bool(lanes)
        return out
    
    @staticmethod
    def Handle(int lanes=1):
        out = Type()
        out.__this__ = Type_Handle(lanes, NULL)
        return out


cdef class Target:
    """ Cython wrapper class for Halide::Target """
    
    cdef:
        HalTarget __this__
    
    @staticmethod
    def validate_target_string(target_string):
        return HalTarget.validate_target_string(target_string)
    
    def __init__(Target self, *args, **kwargs):
        target_string = ''
        if 'target_string' in kwargs:
            target_string = kwargs.get('target_string')
        elif len(args) > 0:
            target_string = args[0]
        if target_string:
            if not HalTarget.validate_target_string(target_string):
                raise ValueError("invalid target string: %s" % target_string)
            self.__this__ = HalTarget(target_string)
    
    property os:
        
        def __get__(Target self):
            return self.__this__.os
            
        def __set__(Target self, value):
            self.__this__.os = <HalTarget.OS>value
        
    property arch:
        
        def __get__(Target self):
            return self.__this__.arch
        
        def __set__(Target self, value):
            self.__this__.arch = <HalTarget.Arch>value
        
    property bits:
        
        def __get__(Target self):
            return self.__this__.bits
        
        def __set__(Target self, value):
            self.__this__.bits = <int>value
    
    def has_gpu_feature(Target self):
        return self.__this__.has_gpu_feature()
    
    def includes_halide_runtime(Target self):
        try:
            return str(self).index('no_runtime') < 0
        except ValueError:
            return True
    
    def to_string(Target self):
        return self.__this__.to_string()
    
    def maximum_buffer_size(Target self):
        return self.__this__.maximum_buffer_size()
    
    def supported(Target self):
        return self.__this__.supported()
    
    def supports_type(Target self, Type t):
        return self.__this__.supports_type(t.__this__)
    
    def natural_vector_size(Target self, Type t):
        return self.__this__.natural_vector_size(t.__this__)
    
    def __str__(Target self):
        return self.__this__.to_string()


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

