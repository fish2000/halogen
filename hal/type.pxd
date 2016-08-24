
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from runtime cimport halide_type_code_t, halide_type_t

# ctypedef vector[string] stringvec_t
# ctypedef vector[halide_cplusplus_type_name] cppnamevec_t

# cdef extern from "Halide.h" namespace "Halide::halide_handle_cplusplus_type":
#
#     cdef enum Modifier(uint8_t):
#         Const
#         Volatile
#         Restrict
#         Pointer


cdef extern from "Halide.h" namespace "Halide::Type":

    cdef halide_type_code_t Int = halide_type_int
    cdef halide_type_code_t UInt = halide_type_uint
    cdef halide_type_code_t Float = halide_type_float
    cdef halide_type_code_t Handle = halide_type_handle


cdef extern from "Halide.h" namespace "Halide":
    
    # cppclass halide_handle_cplusplus_type:
    #
    #     cdef halide_cplusplus_type_name inner_name
    #     cdef stringvec_t namespaces
    #     cdef cppnamevec_t enclosing_types
        
    
    cppclass Type:
        
        # cdef halide_handle_cplusplus_type* handle_type
        
        Type()
        # Type(halide_type_code_t, uint8_t, int, halide_handle_cplusplus_type*)
        Type(Type&)
        # Type(halide_type_t&, halide_handle_cplusplus_type*)
        
        halide_type_code_t code()
        int bytes()
        int bits()
        int lanes()
        
        Type with_code(halide_type_code_t)
        Type with_bits(uint8_t)
        Type with_lanes(uint16_t)
        
        bint is_bool()
        bint is_vector()
        bint is_scalar()
        bint is_float()
        bint is_int()
        bint is_uint()
        bint is_handle()
        bint same_handle_type(Type&)
        
        bint operator==(Type&)
        bint operator!=(Type&)
        
        Type element_of()
        bint can_represent(Type&)
        bint can_represent(double)
        bint can_represent(int64_t)
        bint can_represent(uint64_t)
        
        bint is_max(uint64_t)
        bint is_max(int64_t)
        bint is_min(uint64_t)
        bint is_min(int64_t)
    
    Type Int(int bits, int lanes)
    Type UInt(int bits, int lanes)
    Type Float(int bits, int lanes)
    Type Bool(int lanes)
    Type Handle(int bits, int lanes)
    