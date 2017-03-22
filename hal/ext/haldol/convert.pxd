
from libc.stdint cimport *
from libcpp cimport nullptr_t
from libcpp.string cimport string as std_string
from libcpp.string cimport wstring as std_wstring
from libcpp.vector cimport vector
from libcpp.utility cimport pair

from cpython.object cimport PyTypeObject, Py_buffer
from numpy cimport ndarray, dtype

from ..halide.target cimport OS, Arch, Feature

ctypedef vector[string]     stringvec_t
ctypedef vector[uint8_t]    bytevec_t
ctypedef vector[char]       charvec_t

cdef extern from "haldol/include/detail.hh" namespace "py":
    
    object None()
    object True()
    object False()
    
    object boolean(bint)
    object "string"(std_string&)
    object "string"(std_wstring&)
    object "string"(std_string&)
    object "string"(bytevec_t&)
    object "string"(charvec_t&)
    object "string"(char*)
    object "string"(char*, size_t)
    object "string"(char)
    
    object "object"(object)
    object "object"(ndarray)
    object "object"(dtype)
    object "object"(PyTypeObject*)
    
    object convert(object)
    object convert(ndarray)
    object convert(dtype)
    object convert(PyTypeObject*)
    object convert(object)
    object convert(nullptr_t)
    object convert(void)
    object convert(void*)
    object convert(bint) # ?!
    object convert(size_t)
    object convert(Py_ssize_t)
    object convert(int8_t)
    object convert(int16_t)
    object convert(int32_t)
    object convert(int64_t)
    object convert(uint8_t)
    object convert(uint16_t)
    object convert(uint32_t)
    object convert(uint64_t)
    object convert(object)
    object convert(float)
    object convert(double)
    object convert(long double)
    object convert(char*)
    object convert(char*, size_t)
    object convert(std_string&)
    object convert(std_wstring&)
    object convert(std_string&, size_t)
    object convert(std_wstring&, size_t)
    object convert(Py_buffer*)
    
    object convert(...)
    
    auto integralize[EnumType](EnumType)
    
    cdef object integral[EnumType](EnumType)
    cdef object integral(OS)
    cdef object integral(Arch)
    cdef object integral(Feature)