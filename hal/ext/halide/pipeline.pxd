
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr

from argument cimport Argument
from buffer cimport Buffer
from intrusiveptr cimport IntrusivePtr
from outputs cimport Outputs
from realization cimport Realization
from runtime cimport halide_buffer_t
from target cimport Target

ctypedef vector[Argument]           argvec_t
ctypedef vector[Buffer[]]           buffervec_t
ctypedef unique_ptr[buffervec_t]    buffervec_ptr_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass PipelineContents
    
    cppclass Pipeline:
        
        cppclass RealizationArg:
            Realization* r
            halide_buffer_t* buf
            buffervec_ptr_t buffer_list
            
            RealizationArg(Realization&)
            RealizationArg(Realization&&)
            RealizationArg(halide_buffer_t*)
            
            # Other templated constructors also follow
            
            RealizationArg(RealizationArg&&)
            size_t size()
            
            IntrusivePtr[PipelineContents] contents
            
            cppclass JITCallArgs:
                pass
    
    Pipeline()
    # Pipeline(Func)
    # vector[Func] outputs()
    # Func get_func(size_t)
    void compile_to(Outputs&, argvec_t&, string&, Target&)
    
    void compile_to_bitcode(string&, argvec_t&, string&, Target&)
    void compile_to_bitcode(string&, argvec_t&, string&)
    
    void compile_to_llvm_assembly(string&, argvec_t&, string&, Target&)
    void compile_to_llvm_assembly(string&, argvec_t&, string&)
    
    void compile_to_object(string&, argvec_t&, string&, Target&)
    void compile_to_object(string&, argvec_t&, string&)
    
    void compile_to_header(string&, argvec_t&, string&, Target&)
    void compile_to_header(string&, argvec_t&, string&)
    
    void compile_to_assembly(string&, argvec_t&, string&, Target&)
    void compile_to_assembly(string&, argvec_t&, string&)
    
    void compile_to_c(string&, argvec_t&, string&, Target&)
    void compile_to_c(string&, argvec_t&, string&)
    
    void compile_to_python_extension(string&, argvec_t&, string&, Target&)
    void compile_to_python_extension(string&, argvec_t&, string&)
    
    void compile_to_lowered_stmt(string&, argvec_t&, string&, Target&)
    void compile_to_lowered_stmt(string&, argvec_t&, string&)
    
    