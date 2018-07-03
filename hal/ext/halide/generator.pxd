
from libc.stdint cimport *
from libcpp.map cimport map as std_map
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr, shared_ptr
from libcpp.pair cimport pair

from autoschedule cimport MachineParams
from buffer cimport Buffer
from device_api cimport DeviceAPI
from dimension cimport Dimension
from expr cimport Expr
from externalcode cimport ExternalCode
from func cimport FuncRef
# from function cimport NameMangling, ExternFuncArgument # used in disabled conversion operators
from image cimport OutputImageParam, ImageParam
from module cimport Module, LinkageType
from parameter cimport Parameter
from pipeline cimport Pipeline
from rdom cimport RVar
from realization cimport Realization
from schedule cimport LoopLevel, llevelmap_t, LoopAlignStrategy, PrefetchBoundStrategy, TailStrategy
from target cimport Target, get_target_from_environment
from type cimport Type
from var cimport Var, varvec_t
from varorrvar cimport VarOrRVar

ctypedef vector[Expr]                                   exprvec_t
ctypedef vector[RVar]                                   rvarvec_t
ctypedef vector[Type]                                   typevec_t
ctypedef vector[VarOrRVar]                              varorvec_t
ctypedef vector[string]                                 stringvec_t
ctypedef std_map[string, string]                        stringmap_t
ctypedef std_map[string, Type]                          typemap_t
ctypedef vector[pair[VarOrRVar, LoopAlignStrategy]]     varorpairvec_t

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
    
    cppclass Func
    
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
    
    cppclass GeneratorBase # FORWARD!!
    
    cppclass IOKind:
        pass

ctypedef unique_ptr[GeneratorBase]      base_ptr_t
ctypedef shared_ptr[GeneratorBase]      base_shared_ptr_t

cdef extern from "Halide.h" namespace "Halide::Internal::IOKind" nogil:
    
    # I think all three of these are namespace catastrophes somehow: 
    cdef IOKind IOScalar    "Scalar"
    cdef IOKind IOFunction  "Function"
    cdef IOKind IOBuffer    "Buffer"
    
cdef extern from "Halide.h" namespace "Halide::Internal" nogil:

    cppclass StubInputBuffer[T]: # T = void
        StubInputBuffer()
        # StubInputBuffer[T2](Buffer[T2]&)
    
    cppclass StubOutputBufferBase:
        Realization realize(signedsizevec_t)
        Realization realize(...)
        void realize[Dst](Dst)
    
    cppclass StubOutputBuffer[T](StubOutputBufferBase): # T = void
        StubOutputBuffer()
        StubOutputBuffer(Func&, base_shared_ptr_t)
    
    cppclass StubInput:
        # StubInput[T2](StubInputBuffer[T2]&)
        StubInput(Func&)
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
        vector[Func]& funcs()
        exprvec_t& exprs()
    
    cppclass GeneratorInputBase(GIOBase):
        # Everything in this class is protected
        pass
    
    cppclass GeneratorInputImpl[T, ValueType](GeneratorInputBase):
        size_t size()
        ValueType& operator[](size_t)
        ValueType& at(size_t)
        vector[ValueType].const_iterator begin()
        vector[ValueType].const_iterator end()
    
    cppclass GeneratorInput_Buffer[T](GeneratorInputImpl[T, Func]):
        GeneratorInput_Buffer(string&)
        GeneratorInput_Buffer(string&, Type&, int)
        GeneratorInput_Buffer(string&, Type&)
        GeneratorInput_Buffer(string&, int)
        
        Expr operator()(...)
        Expr operator()(exprvec_t)
        
        # operator StubInputBuffer[T2]()
        # operator Func()
        # operator ExternFuncArgument()
        GeneratorInput_Buffer[T]& estimate(Var, Expr, Expr)
        
        Func func_in "in"()
        Func func_in "in"(Func)
        Func func_in "in"(vector[Func]&)
        
        # operator ImageParam()
        size_t size()
        ImageParam operator[][T2](size_t)
        ImageParam at[T2](size_t)
        vector[ImageParam].const_iterator begin()
        vector[ImageParam].const_iterator end()
        
        Dimension dim(int)
        int host_alignment()
        OutputImageParam& set_host_alignment()
        int dimensions()
        Expr left()
        Expr right()
        Expr top()
        Expr bottom()
        Expr width()
        Expr height()
        Expr channels()
        void trace_loads()
        ImageParam& add_trace_tag(string&)
    
    cppclass GeneratorInput_Func[T](GeneratorInputImpl[T, Func]):
        GeneratorInput_Func(string&, Type&, int)
        GeneratorInput_Func(string&, int)
        GeneratorInput_Func(string&, Type&)
        GeneratorInput_Func(string&)
        GeneratorInput_Func(size_t, string&, Type&, int)
        GeneratorInput_Func(size_t, string&, int)
        GeneratorInput_Func(size_t, string&, Type&)
        GeneratorInput_Func(size_t, string&)
        
        Expr operator()(...)
        Expr operator()(exprvec_t)
        
        # operator Func()
        # operator ExternFuncArgument()
        GeneratorInput_Func[T]& estimate(Var, Expr, Expr)
        
        Func func_in "in"()
        Func func_in "in"(Func)
        Func func_in "in"(vector[Func]&)
        
        varvec_t args()
        bint defined()
        bint has_update_definition()
        int num_update_definitions()
        typevec_t& output_types()
        int outputs()
        rvarvec_t rvars()
        exprvec_t& update_args(int)
        exprvec_t& update_args()
        Expr update_value(int)
        Expr update_value()
        # Tuple update_values(int)
        # Tuple update_values()
        Expr value()
        # Tuple values()
    
    cppclass GeneratorInput_Scalar[T](GeneratorInputImpl[T, Expr]):
        
        # ctypedef GeneratorInputImpl[T, Expr] Super
        # ctypedef Super.TBase TBase
        
        # GeneratorInput_Scalar(string&, TBase&)
        GeneratorInput_Scalar(string&, T&)
        GeneratorInput_Scalar(string&)
        # GeneratorInput_Scalar(size_t, string&, TBase&)
        GeneratorInput_Scalar(size_t, string&, T&)
        GeneratorInput_Scalar(size_t, string&)
        
        # operator Expr()
        # operator ExternFuncArgument()
        void set_estimate(T&)
    
    cppclass GeneratorInput_Arithmetic[T](GeneratorInput_Scalar[T]):
        
        # ctypedef GeneratorInputImpl[T, Expr] Super
        # ctypedef Super.TBase TBase
        
        # GeneratorInput_Arithmetic(string&, TBase&)
        GeneratorInput_Arithmetic(string&, T&)
        GeneratorInput_Arithmetic(string&)
        # GeneratorInput_Arithmetic(size_t, string&, TBase&)
        GeneratorInput_Arithmetic(size_t, string&, T&)
        GeneratorInput_Arithmetic(size_t, string&)
        # GeneratorInput_Arithmetic(string&, TBase&, TBase&, TBase&)
        # GeneratorInput_Arithmetic(size_t, string&, TBase&, TBase&, TBase&)
        GeneratorInput_Arithmetic(string&, T&, T&, T&)
        GeneratorInput_Arithmetic(size_t, string&, T&, T&, T&)
    
    cppclass GeneratorInputImplBase[T](GeneratorInputBase):
        # Declaring the greatest-common-ancestor (if that makes sense)
        # of the type-union-ish thing that this class actually is in
        # the Halide header
        pass

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass GeneratorInput[T](GeneratorInputImplBase[T]):
        
        # ctypedef GeneratorInputImplBase[T] Super
        # ctypedef Super.TBase TBase
        
        cppclass IntIfNonScalar:
            # In reality this is a bizarre “using” statement using
            # lots of STL type-traits to become what it says it is
            pass
        
        GeneratorInput(string&)
        # GeneratorInput(string&, TBase&)
        # GeneratorInput(size_t, string&, TBase&)
        # GeneratorInput(string&, TBase&, TBase&, TBase&)
        # GeneratorInput(size_t, string&, TBase&, TBase&, TBase&)
        GeneratorInput(string&, T&)
        GeneratorInput(size_t, string&, T&)
        GeneratorInput(string&, T&, T&, T&)
        GeneratorInput(size_t, string&, T&, T&, T&)
        GeneratorInput(string&, Type&, int)
        GeneratorInput(string&, Type&)
        GeneratorInput(size_t, string&, IntIfNonScalar)
        GeneratorInput(size_t, string&)

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass Stage
    
    cppclass GeneratorOutputBase(GIOBase):
        T2 as[T2]()
        
        # Forwarded `Func` methods: 
        Func& add_trace_tag(string&)
        Func& align_bounds(Var, Expr, Expr)
        Func& align_bounds(Var, Expr)
        Func& align_storage(Var, Expr)
        varvec_t& args()
        Func& bound(Var, Expr, Expr)
        Func& bound_extent(Var, Expr)
        Func& compute_at(Func, Var)
        Func& compute_at(Func, RVar)
        Func& compute_at(LoopLevel)
        Func& compute_inline()
        Func& compute_root()
        Func& compute_with(Stage, VarOrRVar, varorpairvec_t&)
        Func& compute_with(Stage, VarOrRVar, LoopAlignStrategy)
        Func& compute_with(Stage, VarOrRVar) # LoopAlignStrategy = Auto
        Func& compute_with(LoopLevel, varorpairvec_t&)
        Func& compute_with(LoopLevel, LoopAlignStrategy)
        Func& compute_with(LoopLevel) # LoopAlignStrategy = Auto
        # define_extern()
        bint defined()
        Func& estimate(Var, Expr, Expr)
        Func& fold_storage(Var, Expr, bint)
        Func& fold_storage(Var, Expr)
        Func& fuse(VarOrRVar, VarOrRVar, VarOrRVar)
        Func& glsl(Var, Var, Var)
        Func& gpu_threads(VarOrRVar, DeviceAPI)
        Func& gpu_threads(VarOrRVar) # DeviceAPI = Default_GPU
        Func& gpu_threads(VarOrRVar, VarOrRVar, DeviceAPI)
        Func& gpu_threads(VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        Func& gpu_threads(VarOrRVar, VarOrRVar, VarOrRVar, DeviceAPI)
        Func& gpu_threads(VarOrRVar, VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        Func& gpu_lanes(VarOrRVar, DeviceAPI)
        Func& gpu_lanes(VarOrRVar) # DeviceAPI = Default_GPU
        Func& gpu_single_thread(DeviceAPI)
        Func& gpu_single_thread() # DeviceAPI = Default_GPU
        Func& gpu_blocks(VarOrRVar, DeviceAPI)
        Func& gpu_blocks(VarOrRVar) # DeviceAPI = Default_GPU
        Func& gpu_blocks(VarOrRVar, VarOrRVar, DeviceAPI)
        Func& gpu_blocks(VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        Func& gpu_blocks(VarOrRVar, VarOrRVar, VarOrRVar, DeviceAPI)
        Func& gpu_blocks(VarOrRVar, VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU

        Func& gpu(VarOrRVar, VarOrRVar, DeviceAPI)
        Func& gpu(VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        Func& gpu(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, DeviceAPI)
        Func& gpu(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        Func& gpu(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, DeviceAPI)
        Func& gpu(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU

        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, Expr, TailStrategy, DeviceAPI)
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        Func& gpu_tile(VarOrRVar, VarOrRVar, Expr, TailStrategy, DeviceAPI)
        Func& gpu_tile(VarOrRVar, VarOrRVar, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Func& gpu_tile(VarOrRVar, VarOrRVar, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy, DeviceAPI)
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy, DeviceAPI)
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr, TailStrategy, DeviceAPI)
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr, TailStrategy, DeviceAPI)
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Func& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        bint has_update_definition()
        Func& hexagon(VarOrRVar)
        Func& hexagon()
        Func func_in "in"(Func&)
        Func func_in "in"(vector[Func]&)
        Func func_in "in"()
        Func& memoize()
        int num_update_definitions()
        typevec_t& output_types()
        int outputs()
        Func& parallel(VarOrRVar)
        Func& parallel(VarOrRVar, Expr, TailStrategy)
        Func& parallel(VarOrRVar, Expr) # TailStrategy = Auto
        Func& prefetch(Func&, VarOrRVar, Expr, PrefetchBoundStrategy)
        Func& prefetch(Func&, VarOrRVar, Expr)
        Func& prefetch(Func&, VarOrRVar)
        Func& prefetch(Parameter&, VarOrRVar, Expr, PrefetchBoundStrategy)
        Func& prefetch(Parameter&, VarOrRVar, Expr)
        Func& prefetch(Parameter&, VarOrRVar)
        Func& prefetch[T](T&, VarOrRVar, Expr, PrefetchBoundStrategy)
        Func& prefetch[T](T&, VarOrRVar, Expr)
        Func& prefetch[T](T&, VarOrRVar)
        void print_loop_nest()
        Func& rename(VarOrRVar, VarOrRVar)
        Func& reorder(varorvec_t&)
        Func& reorder(VarOrRVar, VarOrRVar, ...)
        Func& reorder_storage(varvec_t&)
        rvarvec_t rvars(int)
        rvarvec_t rvars()
        Func& serial(VarOrRVar)
        Func& shader(Var, Var, Var, DeviceAPI)
        Stage specialize(Expr)
        void specialize_fail(string&)
        Func& split(VarOrRVar, VarOrRVar, VarOrRVar, Expr, TailStrategy)
        Func& split(VarOrRVar, VarOrRVar, VarOrRVar, Expr) # TailStrategy = Auto
        Func& store_at(Func, Var)
        Func& store_at(Func, RVar)
        Func& store_at(LoopLevel)
        Func& store_root()
        Func& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy)
        Func& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr) # TailStrategy = Auto
        Func& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy)
        Func& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr) # TailStrategy = Auto
        Func& trace_stores()
        Func& unroll(VarOrRVar)
        Func& unroll(VarOrRVar, Expr, TailStrategy)
        Func& unroll(VarOrRVar, Expr) # TailStrategy = Auto
        Stage update(int)
        Stage update()
        exprvec_t& update_args(int)
        exprvec_t& update_args()
        Expr update_value(int)
        Expr update_value()
        # Tuple update_values(int)
        # Tuple update_values()
        Expr value()
        # Tuple values()
        Func& vectorize(VarOrRVar)
        Func& vectorize(VarOrRVar, Expr, TailStrategy)
        Func& vectorize(VarOrRVar, Expr) # TailStrategy = Auto
        Func& vectorize()
    
    cppclass GeneratorOutputImpl[T](GeneratorOutputBase):
        
        bint is_array()
        
        GeneratorOutputImpl(string&, IOKind, typevec_t&, int)
        
        FuncRef operator()(...)
        FuncRef operator()[ExprOrVar](vector[ExprOrVar])
        
        # operator Func()
        # operator Stage()
        size_t size()
        Func& operator[](size_t)
        Func& at(size_t)
        vector[Func].const_iterator begin()
        vector[Func].const_iterator end()
        void resize(size_t)
    
    cppclass GeneratorOutput_Buffer[T](GeneratorOutputImpl[T]):
        
        GeneratorOutput_Buffer[T]& operator=[T2](Buffer[T2]&)
        GeneratorOutput_Buffer[T]& operator=[T2](StubOutputBuffer[T2]&)
        GeneratorOutput_Buffer[T]& operator=(Func&)
        # operator OutputImageParam()
        
        # Forwarded `OutputImageParam` methods:
        Dimension dim(int)
        int host_alignment()
        OutputImageParam& set_host_alignment(int)
        int dimensions()
        Expr left()
        Expr right()
        Expr top()
        Expr bottom()
        Expr width()
        Expr height()
        Expr channels()
    
    cppclass GeneratorOutput_Func[T](GeneratorOutputImpl[T]):
        
        GeneratorOutput_Func[T]& operator=(Func&)
        Func& operator[](size_t)
        GeneratorOutput_Func[T]& estimate(Var, Expr, Expr)
    
    cppclass GeneratorOutput_Arithmetic[T](GeneratorOutputImpl[T]):
        
        GeneratorOutput_Arithmetic(string&)
        GeneratorOutput_Arithmetic(size_t, string&)
    
    cppclass GeneratorOutputImplBase[T](GeneratorOutputImpl[T]):
        # Declaring the greatest-common-ancestor (if that makes sense)
        # of the type-union-ish thing that this class actually is in
        # the Halide header
        pass

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass GeneratorOutput[T](GeneratorOutputImplBase[T]):
        
        GeneratorOutput(string&)
        GeneratorOutput(char*)
        GeneratorOutput(size_t, string&)
        GeneratorOutput(string&, int)
        GeneratorOutput(string&, Type&, int)
        GeneratorOutput(string&, typevec_t&, int)
        GeneratorOutput(size_t, string&, int)
        GeneratorOutput(size_t, string&, Type&, int)
        GeneratorOutput(size_t, string&, typevec_t&, int)
        
        GeneratorOutput[T]& operator=[T2](Buffer[T2]&)
        GeneratorOutput[T]& operator=[T2](StubOutputBuffer[T2]&)
        GeneratorOutput[T]& operator=(Func&)

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    T parse_scalar[T](string&)
    typevec_t parse_halide_type_list(string&)
    
    cppclass SyntheticParamType:
        pass

cdef extern from "Halide.h" namespace "Halide::Internal::SyntheticParamType" nogil:
    
    cdef SyntheticParamType SyntheticType       "Type"
    cdef SyntheticParamType SyntheticDim        "Dim"
    cdef SyntheticParamType SyntheticArraySize  "ArraySize"

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass GeneratorParam_Synthetic[T](GeneratorParamImpl[T]):
        
        void set_from_string(string&)
        string get_default_value()
        string call_to_string(string&)
        string get_c_type()
        bint is_synthetic_param()
    
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
        
        void set_generator_param_values(GeneratorParamsMap&)
        
        int natural_vector_size(Type)
        int natural_vector_size[data_t]()
        
        void emit_cpp_stub(string&)
        
        Module build_module(string&, LinkageType)
        Module build_module(string&) # LinkageType = ExternalPlusMetadata
        Module build_module() # function_name = generator_name(),
                              # LinkageType = ExternalPlusMetadata
        
        void set_inputs(...)
        Realization realize(signedsizevec_t)
        Realization realize(...)
        void realize(Realization)
        Pipeline get_pipeline()

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:

    cppclass GeneratorFactory:
        # In real life, this is defined as a:
        # std::function<std::unique_ptr<Halide::GeneratorBase>(Halide::GeneratorContext const&)>
        base_ptr_t operator()(GeneratorContext&)
    
    cppclass SimpleGeneratorFactory(GeneratorFactory):
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
        
        vector[vector[Func]] generate(GeneratorParamsMap&, stubinputvecvec_t&)
        
        Func get_output(string&)
        T2 get_output_buffer[T2](string&)
        vector[T2] get_array_output_buffer[T2](string&)
        vector[Func] get_array_output(string&)
        
        @staticmethod
        stubinputvec_t to_stub_input_vector(Expr&)
        
        @staticmethod
        stubinputvec_t to_stub_input_vector(Func&)
        
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
