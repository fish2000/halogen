
from libc.stdint cimport *
from libcpp.map cimport map as std_map
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr

from intrusiveptr cimport IntrusivePtr
from llvm cimport LLVMModule, LLVMType
from module cimport Module, LoweredFunc, modulevec_t
from pipeline cimport ExternCFunction
from target cimport Target

ctypedef vector[string]         stringvec_t
ctypedef unique_ptr[Module]     moduleptr_t
    
cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    # in the C++ header, this is a forward declaration:
    cppclass JITModuleContents:
        pass
    
    cppclass JITModule

ctypedef IntrusivePtr[JITModuleContents]    jitcontentsptr_t
ctypedef vector[JITModule]                  jitmodulevec_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass JITModule:
        
        jitcontentsptr_t jit_module
        
        cppclass Symbol:
            void* address
            LLVMType* llvm_type
            Symbol()
            Symbol(void*, LLVMType*)
        
        ctypedef std_map[string, Symbol]    symbolmap_t
        
        JITModule()
        JITModule(Module&, LoweredFunc&, jitmodulevec_t&)
        
        symbolmap_t& exports()
        void* main_function()
        Symbol entrypoint_symbol()
        Symbol argv_entrypoint_symbol()
        # argv_wrapper argv_function()
        
        void add_dependency(JITModule&)
        void add_symbol_for_export(string&, Symbol&)
        void add_extern_for_export(string&, ExternCFunction&)
        Symbol find_symbol_by_name(string&)
        
        void compile_module(moduleptr_t,     string&,   Target&,
                            jitmodulevec_t&, stringvec_t)
        
        void memoization_cache_set_size(int64_t)
        
        bint compiled()
    
    cppclass JITHandlers:
        pass
    
    cppclass JITUserContext:
        void* user_context
        JITHandlers handlers
    
    cppclass JITSharedRuntime:
        
        @staticmethod
        jitmodulevec_t get(LLVMModule*, Target&)
        
        @staticmethod
        jitmodulevec_t get(LLVMModule*, Target&, bint create)
        
        @staticmethod
        void init_jit_user_context(JITUserContext&, void*, JITHandlers&)
        
        @staticmethod
        JITHandlers set_default_handlers(JITHandlers&)
        
        @staticmethod
        void memoization_cache_set_size(int64_t)
        
        @staticmethod
        void release_all()
