
from libc.stdint cimport *
from libcpp.map cimport map as std_map
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr

from argument cimport Argument
from autoschedule cimport MachineParams
from buffer cimport Buffer
from expr cimport Stmt
from intrusiveptr cimport IntrusivePtr
from module cimport Module, LinkageType
from module cimport ExternalPlusMetadata as Linkage_ExternalPlusMetadata
from outputs cimport Outputs
from realization cimport Realization
from runtime cimport halide_buffer_t
from target cimport Target
from type cimport Type

ctypedef vector[Argument]           argvec_t
ctypedef vector[Buffer[void]]       buffervec_t
ctypedef vector[Target]             targetvec_t
ctypedef vector[Type]               typevec_t
ctypedef unique_ptr[buffervec_t]    buffervec_ptr_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cdef cppclass StmtOutputFormat:
        pass

cdef extern from "Halide.h" namespace "Halide::StmtOutputFormat" nogil:
    
    cdef StmtOutputFormat Text
    cdef StmtOutputFormat HTML
    
cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass CustomLoweringPass:
        pass
    
    cppclass JITExtern:
        pass
    
ctypedef vector[CustomLoweringPass] custompassvec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Func
    
    cppclass PipelineContents:
        pass
    
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
        
        argvec_t infer_arguments(Stmt)
        
        cppclass JITCallArgs:
            pass
        
        # void prepare_jit_call_arguments(RealizationArg&, Target&, ParamMap&, void*, bint, JITCallArgs&)
        
        # @staticmethod
        # vector[JITModule] make_externs_jit_module(Target&, std_map[string, JITExtern]&)
        
        Pipeline()
        Pipeline(Func)
        Pipeline(vector[Func]&)
        vector[Func] outputs()
        
        string auto_schedule(Target&, MachineParams&)
        string auto_schedule(Target&)
        
        Func get_func(size_t)
        
        void compile_to(Outputs&, argvec_t&, string&, Target&)
        void compile_to(Outputs&, argvec_t&, string&)
        
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
        
        void compile_to_lowered_stmt(string&, argvec_t&, StmtOutputFormat, Target&)
        void compile_to_lowered_stmt(string&, argvec_t&, StmtOutputFormat)
        void compile_to_lowered_stmt(string&, argvec_t&)
        
        void print_loop_nest();
        
        void compile_to_file(string&, argvec_t&, string&, Target&)
        void compile_to_file(string&, argvec_t&, string&)
        
        void compile_to_static_library(string&, argvec_t&, string&, Target&)
        void compile_to_static_library(string&, argvec_t&, string&)
        
        void compile_to_multitarget_static_library(string&, argvec_t&, targetvec_t&)
        
        Module compile_to_module(argvec_t&, string&, Target&, LinkageType)
        Module compile_to_module(argvec_t&, string&, Target&)
        Module compile_to_module(argvec_t&, string&)
        
        void* compile_jit(Target&)
        void* compile_jit()
        
        # These functions take function pointers:
        # void set_error_handler(…)
        # void set_custom_allocator(…)
        # void set_custom_do_task(…)
        # void set_custom_do_par_for(…)
        # void set_custom_trace(…)
        # void set_custom_print(…)
        # void set_jit_externs(…)
        
        void add_custom_lowering_pass[T](T*)
        # void add_custom_lowering_pass(IRMutator2*, function[void()])
        void clear_custom_lowering_passes()
        custompassvec_t& custom_lowering_passes()
        
        # INSERT REALIZATIONS HERE
        
        argvec_t infer_arguments()
        bint defined()
        void invalidate_cache()
    
    
    cppclass ExternSignature:
        
        ExternSignature()
        ExternSignature(Type&, bint, typevec_t&)
        
        Type& ret_type()
        bint is_void_return()
        typevec_t& arg_types()
    
    
    cppclass ExternCFunction:
        
        ExternCFunction()
        ExternCFunction(void*, ExternSignature&)
        
        void* address()
        ExternSignature& signature()
    
    
    cppclass JITExtern:
        
        JITExtern(Pipeline)
        JITExtern(Func)
        JITExtern(ExternCFunction&)
        
        Pipeline& pipeline()
        ExternCFunction& extern_c_function()

