
from libc.stdint cimport *
from libcpp.map cimport map as std_map
from libcpp.string cimport string
from libcpp.vector cimport vector
from runtime cimport halide_type_code_t, halide_type_t

ctypedef vector[string]     stringvec_t
ctypedef vector[uint8_t]    bytevec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass LoopLevel:
        # string func_name
        # string var_name
        # bint is_rvar
        # LoopLevel(string&, string&, bint)
        LoopLevel()


cdef extern from "Halide.h" namespace "halide_cplusplus_type_name":
    
    cdef enum CPPTypeType:
        Simple
        Struct
        Class
        Union
        Enum


cdef extern from "Halide.h":
    
    cppclass halide_cplusplus_type_name:
        
        CPPTypeType cpp_type_type
        string name
        
        halide_cplusplus_type_name(CPPTypeType, string&)
        bint operator==(halide_cplusplus_type_name&)
        bint operator!=(halide_cplusplus_type_name&)
        bint operator<(halide_cplusplus_type_name&)


ctypedef vector[halide_cplusplus_type_name] cppnamevec_t

cdef extern from "Halide.h" namespace "halide_handle_cplusplus_type":
    
    cdef enum Modifier:
        Const
        Volatile
        Restrict
        Pointer
    
    cppclass CPPTypeModifiers:
        uint8_t data[8]
        
        CPPTypeModifiers(bytevec_t&)
        uint8_t& operator[](size_t)
        bint operator==(CPPTypeModifiers&)
        uint8_t* begin()
        uint8_t* end()
    
    cdef enum ReferenceType:
        NotReference
        LValueReference
        RValueReference


cdef extern from "Halide.h":
    
    cppclass halide_handle_cplusplus_type:
        
        halide_cplusplus_type_name inner_name
        stringvec_t namespaces
        cppnamevec_t enclosing_types
        CPPTypeModifiers cpp_type_modifiers
        ReferenceType reference_type
        
        halide_handle_cplusplus_type(halide_cplusplus_type_name&,
                                     stringvec_t&, cppnamevec_t&, bytevec_t&,
                                     ReferenceType)


cdef extern from "Halide.h" namespace "Halide::Type":
    
    cdef halide_type_code_t Int = halide_type_int
    cdef halide_type_code_t UInt = halide_type_uint
    cdef halide_type_code_t Float = halide_type_float
    cdef halide_type_code_t Handle = halide_type_handle


cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Type:
        
        halide_handle_cplusplus_type* handle_type
        
        Type()
        Type(Type&)
        Type(halide_type_code_t, uint8_t, int, halide_handle_cplusplus_type*)
        Type(halide_type_t&, halide_handle_cplusplus_type*)
        
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
    Type Handle(int lanes, halide_handle_cplusplus_type* handle_type)

ctypedef std_map[string, LoopLevel]     llevelmap_t
ctypedef std_map[string, Type]          haltypemap_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    # These functions, at time of writing, are prototyped out in Generator.h:
    
    haltypemap_t& get_halide_type_enum_map()
    string halide_type_to_enum_string(Type&)
    
    LoopLevel get_halide_undefined_looplevel()
    llevelmap_t& get_halide_looplevel_enum_map()
    string halide_looplevel_to_enum_string(LoopLevel&)
    
    string halide_type_to_c_source(Type&)
    string halide_type_to_c_type(Type&)