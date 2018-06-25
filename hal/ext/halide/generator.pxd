
from libc.stdint cimport *
from libcpp.map cimport map as std_map
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr, shared_ptr

from autoschedule cimport MachineParams
from buffer cimport Buffer
from expr cimport Expr
from externalcode cimport ExternalCode
from pipeline cimport Pipeline
from realization cimport Realization
from schedule cimport LoopLevel, llevelmap_t
from target cimport Target, get_target_from_environment
from type cimport Type
from module cimport Module, LinkageType

ctypedef vector[Expr]                   exprvec_t
ctypedef vector[Type]                   typevec_t
ctypedef vector[string]                 stringvec_t
ctypedef std_map[string, string]        stringmap_t
ctypedef std_map[string, Type]          typemap_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass ValueTracker:
        ValueTracker()
        ValueTracker(size_t)
        void track_values(string&, exprvec_t&)
    
    string enum_to_string[T](std_map[string, T]&, T&)
    T enum_from_string[T](std_map[string, T]&, string&)
    typemap_t& get_halide_type_enum_map()
    string halide_type_to_enum_string(Type&)
    
    cppclass GeneratorParamBase:
        string name
        GeneratorParamBase(string&)
        GeneratorParamBase(GeneratorParamBase&)
    
    cppclass GeneratorParamImpl[T](GeneratorParamBase):
        GeneratorParamImpl(string&, T&)
        T value()
        # operator T()
        # operator Expr()
        void set(bint&)
        void set(int8_t&)
        void set(int16_t&)
        void set(int32_t&)
        void set(int64_t&)
        void set(uint8_t&)
        void set(uint16_t&)
        void set(uint32_t&)
        void set(uint64_t&)
        void set(float&)
        void set(double&)
        void set(Target&)
        void set(MachineParams&)
        void set(Type&)
        void set(LoopLevel&)
    
    cppclass GeneratorParam_Target[T](GeneratorParamImpl[T]):
        GeneratorParam_Target(string&, T&)
        void set_from_string(string&)
        string get_default_value()
        string call_to_string(string&)
        string get_c_type()
    
    cppclass GeneratorParam_MachineParams[T](GeneratorParamImpl[T]):
        GeneratorParam_MachineParams(string&, T&)
        void set_from_string(string&)
        string get_default_value()
        string call_to_string(string&)
        string get_c_type()
    
    cppclass GeneratorParam_LoopLevel(GeneratorParamImpl[LoopLevel]):
        GeneratorParam_LoopLevel(string&, LoopLevel&)
        void set(LoopLevel&)
        void set_from_string(string&)
        string get_default_value()
        string call_to_string(string&)
        string get_c_type()
        bint is_looplevel_param()
    
    cppclass GeneratorParam_Arithmetic[T](GeneratorParamImpl[T]):
        GeneratorParam_Arithmetic(string&, T&)          # value
        GeneratorParam_Arithmetic(string&, T&, T&)      # value, min
        GeneratorParam_Arithmetic(string&, T&, T&, T&)  # value, min, max
        void set_impl(T&)
        void set_from_string(string&)
        string get_default_value()
        string call_to_string(string&)
        string get_c_type()
    
    cppclass GeneratorParam_Bool[T](GeneratorParam_Arithmetic[T]):
        GeneratorParam_Bool(string&, T&)
        void set_from_string(string&)
        string get_default_value()
        string call_to_string(string&)
        string get_c_type()
    
    cppclass GeneratorParam_Enum[T](GeneratorParamImpl[T]):
        GeneratorParam_Enum(string&, T&, std_map[string, T]&)
        void set(T&)
        void set_from_string(string&)
        string get_default_value()
        string call_to_string(string&)
        string get_c_type()
        string get_type_decls()
    
    cppclass GeneratorParam_Type[T](GeneratorParam_Enum[T]):
        GeneratorParam_Type(string&, T&)
        string call_to_string(string&)
        string get_c_type()
        string get_default_value()
        string get_type_decls()
    
    cppclass GeneratorParamImplBase[T]:
        pass
    
cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass GeneratorParam[T](GeneratorParamImplBase[T]):
        GeneratorParam(string&, T&)                         # name, value
        GeneratorParam(string&, T&, T&, T&)                 # name, value, min, max
        GeneratorParam(string&, T&, std_map[string, T]&)    # name, value, enum map
        GeneratorParam(string&, string&)                    # name, value
    
    cppclass GeneratorContext:
        ctypedef std_map[string, ExternalCode] ExternsMap
        ctypedef shared_ptr[ExternsMap] shared_externs_t
        GeneratorContext(Target&)
        GeneratorContext(Target&, bint)
        GeneratorContext(Target&, bint, MachineParams&)
        Target get_target()
        bint get_auto_schedule()
        MachineParams get_machine_params()
        
        shared_externs_t get_externs_map()
        unique_ptr[T] create[T]()
        unique_ptr[T] apply[T](...)
    
    cppclass NamesInterface:
        pass

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass StringOrLoopLevel:
        string string_value
        LoopLevel loop_level
        StringOrLoopLevel()
        StringOrLoopLevel(char*)
        StringOrLoopLevel(string&)
        StringOrLoopLevel(LoopLevel&)

ctypedef std_map[string, StringOrLoopLevel] GeneratorParamsMap
ctypedef GeneratorParam[Target]             targetparam_t
ctypedef vector[int32_t]                    signedsizevec_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass IOKind:
        pass
    
cdef extern from "Halide.h" namespace "Halide::Internal::IOKind" nogil:
    
    cdef IOKind Scalar
    cdef IOKind Function
    cdef IOKind Buffer
    
cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass StubInputBuffer[T]: # T = void
        StubInputBuffer()
        # StubInputBuffer[T2](Buffer[T2]&)
    
    cppclass StubOutputBufferBase:
        Realization realize(signedsizevec_t)
        void realize[Dst](Dst)
    
    cppclass StubOutputBuffer[T](StubOutputBufferBase): # T = void
        StubOutputBuffer()
    
    cppclass StubInput:
        # StubInput[T2](StubInputBuffer[T2]&)
        # StubInput(Func&)
        StubInput(Expr&)
    
    cppclass GIOBase:
        bint array_size_defined()
        size_t array_size()
        bint is_array()
        string& name()
        IOKind kind()
        bint types_defined()
        typevec_t& types()
        Type type()
        bint dims_defined()
        int dims()
        # vector[Func]& funcs()
        exprvec_t& exprs()
    
    cppclass GeneratorInputBase(GIOBase):
        pass
    
    cppclass GeneratorInputImpl[T, ValueType](GeneratorInputBase):
        size_t size()
        ValueType& operator[](size_t)
        ValueType& at(size_t)
        # vector[ValueType].const_iterator begin()
        # vector[ValueType].const_iterator end()
    
    # cppclass GeneratorInput_Buffer[T](GeneratorInputImpl[T, Func])
    
    cppclass GeneratorBase(NamesInterface, GeneratorContext):
        
        cppclass EmitOptions:
            bint emit_o
            bint emit_h
            bint emit_cpp
            bint emit_python_extension
            bint emit_assembly
            bint emit_bitcode
            bint emit_stmt
            bint emit_stmt_html
            bint emit_static_library
            bint emit_cpp_stub
            bint emit_schedule
            stringmap_t substitutions
            EmitOptions()
        
        Target get_target()
        
        # void set_generator_param(string&, string&)
        void set_generator_param_values(GeneratorParamsMap&)
        
        # GeneratorBase& set_generator_param[T](string&, T&)
        # GeneratorBase& set_schedule_param[T](string&, T&)
        # void set_schedule_param_values(stringmap_t&, llevelmap_t&)
        
        int natural_vector_size(Type)
        int natural_vector_size[data_t]()
        
        void emit_cpp_stub(string&)
        Module build_module(string&, LinkageType)
        
        void set_inputs(...)
        Realization realize(signedsizevec_t)
        # Realization realize(...)
        void realize(Realization)
        Pipeline get_pipeline()


ctypedef unique_ptr[GeneratorBase]      base_ptr_t
ctypedef shared_ptr[GeneratorBase]      base_shared_ptr_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:

    cppclass GeneratorFactory: # ABSTRACT
        # base_ptr_t create(GeneratorContext&, stringmap_t&)
        pass
    
    # cppclass GeneratorCreateFunc: # FUNCTOR
    #     # std::function<std::unique_ptr<Internal::GeneratorBase>(GeneratorContext const&)>
    #     pass
    
    cppclass SimpleGeneratorFactory(GeneratorFactory):
        # SimpleGeneratorFactory(GeneratorCreateFunc, string&)
        # base_ptr_t create(GeneratorContext&, stringmap_t&)
        pass


ctypedef unique_ptr[GeneratorFactory]   factory_ptr_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass GeneratorRegistry:
        
        @staticmethod
        void register_factory(string&, GeneratorFactory)
        
        @staticmethod
        void unregister_factory(string&)
        
        @staticmethod
        stringvec_t enumerate()
        
        @staticmethod
        base_ptr_t create(string&, GeneratorContext&)


cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Generator[T](GeneratorBase):
        
        @staticmethod
        unique_ptr[T] create(GeneratorContext&)
        
        @staticmethod
        unique_ptr[T] create(GeneratorContext&, string&, string&) # registered name,
                                                                  # stub name
        void apply(...)

ctypedef vector[vector[StubInput]]  stubinputvecvec_t
ctypedef vector[StubInput]          stubinputvec_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass RegisterGenerator:
        RegisterGenerator(char*, GeneratorFactory)
    
    cppclass GeneratorStub(NamesInterface):
        
        GeneratorStub(GeneratorContext&,
                      GeneratorFactory)
        
        GeneratorStub(GeneratorContext&,
                      GeneratorFactory,
                      GeneratorParamsMap&,
                      stubinputvecvec_t&)
        
        # vector[vector[Func]] generate(GeneratorParamsMap&, stubinputvecvec_t&)
        
        # Func get_output(string&)
        T2 get_output_buffer[T2](string&)
        vector[T2] get_array_output_buffer[T2](string&)
        # vector[Func] get_array_output(string&)
        
        @staticmethod
        stubinputvec_t to_stub_input_vector(Expr&)
        
        # @staticmethod
        # stubinputvec_t to_stub_input_vector(Func&)
        
        @staticmethod
        stubinputvec_t to_stub_input_vector[T](StubInputBuffer[T]&)
        
        @staticmethod
        stubinputvec_t to_stub_input_vector[T](vector[T]&)
        
        cppclass Names:
            stringvec_t generator_params
            stringvec_t filter_params
            stringvec_t inputs
            stringvec_t outputs
        
        Names get_names()
        
        base_shared_ptr_t generator

cdef extern from "Halide.h" namespace "halide_register_generator" nogil:
    cppclass halide_global_ns:
        pass


cdef inline base_ptr_t generator_registry_get(string& name,
                                              Target& target,
                                              stringmap_t& args) nogil:
    return GeneratorRegistry.create(name, GeneratorContext(target))

cdef inline base_ptr_t generator_registry_create(string& name) nogil:
    cdef Target t = get_target_from_environment()
    return GeneratorRegistry.create(name, GeneratorContext(t))
