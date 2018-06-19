
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


cdef extern from "Halide.h" namespace "halide_cplusplus_type_name" nogil:
    
    cdef enum CPPTypeType:
        Simple
        Struct
        Class
        Union
        Enum


cdef extern from "Halide.h" nogil:
    
    cppclass halide_cplusplus_type_name:
        
        CPPTypeType cpp_type_type
        string name
        
        halide_cplusplus_type_name(CPPTypeType, string&)
        bint operator==(halide_cplusplus_type_name&)
        bint operator!=(halide_cplusplus_type_name&)
        bint operator<(halide_cplusplus_type_name&)


ctypedef vector[halide_cplusplus_type_name] cppnamevec_t

cdef extern from "Halide.h" namespace "halide_handle_cplusplus_type" nogil:
    
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


cdef extern from "Halide.h" nogil:
    
    cppclass halide_handle_cplusplus_type:
        
        halide_cplusplus_type_name inner_name
        stringvec_t namespaces
        cppnamevec_t enclosing_types
        CPPTypeModifiers cpp_type_modifiers
        ReferenceType reference_type
        
        halide_handle_cplusplus_type(halide_cplusplus_type_name&,
                                     stringvec_t&, cppnamevec_t&, bytevec_t&,
                                     ReferenceType)


cdef extern from "Halide.h" namespace "Halide::Type" nogil:
    
    cdef halide_type_code_t IntCode     "Int" = halide_type_int
    cdef halide_type_code_t UIntCode    "UInt" = halide_type_uint
    cdef halide_type_code_t FloatCode   "Float" = halide_type_float
    cdef halide_type_code_t HandleCode  "Handle" = halide_type_handle


cdef extern from "Halide.h" namespace "Halide":
    
    cppclass Type:
        
        halide_handle_cplusplus_type* handle_type
        
        Type() nogil
        Type(Type&) nogil
        Type(halide_type_code_t, uint8_t, int, halide_handle_cplusplus_type*) except +
        Type(halide_type_t&, halide_handle_cplusplus_type*) except +
        
        halide_type_code_t code() nogil
        int bytes() nogil
        int bits() nogil
        int lanes() nogil
        
        Type with_code(halide_type_code_t) except +
        Type with_bits(uint8_t) except +
        Type with_lanes(uint16_t) except +
        
        bint is_bool() nogil
        bint is_vector() nogil
        bint is_scalar() nogil
        bint is_float() nogil
        bint is_int() nogil
        bint is_uint() nogil
        bint is_handle() nogil
        bint same_handle_type(Type&) nogil
        
        bint operator==(Type&) nogil
        bint operator!=(Type&) nogil
        
        Type element_of() nogil
        bint can_represent(Type&) nogil
        bint can_represent(double) nogil
        bint can_represent(int64_t) nogil
        bint can_represent(uint64_t) nogil
        
        bint is_max(uint64_t) nogil
        bint is_max(int64_t) nogil
        bint is_min(uint64_t) nogil
        bint is_min(int64_t) nogil
    
    Type Int(int bits, int lanes) except +
    Type UInt(int bits, int lanes) except +
    Type Float(int bits, int lanes) except +
    Type Bool(int lanes) except +
    Type Handle(int lanes, halide_handle_cplusplus_type* handle_type) except +

ctypedef std_map[string, LoopLevel]     llevelmap_t
ctypedef std_map[string, Type]          haltypemap_t

cdef extern from "Halide.h" namespace "Halide::Internal":
    
    # These functions, at time of writing, are prototyped out in Generator.h:
    
    haltypemap_t& get_halide_type_enum_map() nogil
    string halide_type_to_enum_string(Type&) except +
    
    LoopLevel get_halide_undefined_looplevel() nogil
    llevelmap_t& get_halide_looplevel_enum_map() nogil
    string halide_looplevel_to_enum_string(LoopLevel&) nogil
    
    string halide_type_to_c_source(Type&) except +
    string halide_type_to_c_type(Type&) except +