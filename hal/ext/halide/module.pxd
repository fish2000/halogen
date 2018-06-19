
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.map cimport map as std_map

from argument cimport Argument, Kind
from buffer cimport Buffer, buffervec_t
from outputs cimport Outputs
from target cimport Target
from type cimport Type

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cdef cppclass LinkageType:
        pass

cdef extern from "Halide.h" namespace "Halide::LinkageType" nogil:
    
    cdef LinkageType External
    cdef LinkageType Internal

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass LoweredArgument(Argument):
        LoweredArgument()
        LoweredArgument(Argument&)
        LoweredArgument(string&, Kind, Type&, uint8_t)

ctypedef vector[LoweredArgument] loweredargvec_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass LoweredFunc:
        string name
        loweredargvec_t args
        LinkageType linkage

ctypedef vector[LoweredFunc] funcvec_t

cdef extern from "Halide.h" namespace "Halide" nogil:

    cppclass Module

ctypedef vector[Module]             modulevec_t
ctypedef std_map[string, string]    stringmap_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Module:
        
        # Module()
        Module(string&, Target&)
        Module(Module&)
        
        Target& target()
        string& name()
        string& auto_schedule()
        bint any_strict_float()
        
        void set_auto_schedule(string&)
        void set_any_strict_float(bint)
        
        buffervec_t& buffers()
        funcvec_t& functions()
        modulevec_t& submodules()
        
        void append(Buffer[void]&)
        void append(LoweredFunc&)
        void append(Module&)
        LoweredFunc get_function_by_name(string&)
        
        void compile(Outputs&)
        Buffer[uint8_t] compile_to_buffer()
        Module resolve_submodules()
        
        void remap_metadata_name(string&, string&) # from, to
        stringmap_t get_metadata_name_map

# ctypedef vector[Module] modulevec_t
ctypedef vector[Target] targetvec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass ModuleProducer:
        pass
    
    Module link_modules(string&, modulevec_t&)
    void halide_compile_standalone_runtime_for_path        "compile_standalone_runtime" (string&, Target)  # creates object file
    Outputs halide_compile_standalone_runtime_with_outputs "compile_standalone_runtime" (Outputs&, Target) # creates object and/or static library
    
    void compile_multitarget(string&, Outputs&, targetvec_t&, ModuleProducer, stringmap_t&)
    void compile_multitarget(string&, Outputs&, targetvec_t&, ModuleProducer)
    