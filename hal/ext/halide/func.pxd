
from libc.stdint cimport *
from libcpp.map cimport map as std_map
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.memory cimport unique_ptr

from argument cimport Argument
from buffers cimport Buffer
from definition cimport Definition
from device_api cimport DeviceAPI
from expr cimport Expr
from function cimport Function, NameMangling, ExternFuncArgument, extargvec_t
from image cimport OutputImageParam
from intrusiveptr cimport IntrusivePtr
from jitmodule cimport JITHandlers
from module cimport Module, LoweredFunc, modulevec_t
from outputs cimport Outputs
from parameter cimport Parameter
from pipeline cimport ExternCFunction, Pipeline, StmtOutputFormat, CustomLoweringPass
from rdom cimport RVar, RDom
from realization cimport Realization
from schedule cimport LoopLevel, LoopAlignStrategy, TailStrategy, PrefetchBoundStrategy
from target cimport Target
from types cimport Type
from var cimport Var, varvec_t
from varorrvar cimport VarOrRVar, varorvec_t

ctypedef vector[int32_t]                                signed_sizevec_t
ctypedef vector[Argument]                               argvec_t
ctypedef vector[CustomLoweringPass]                     customloweringpassvec_t
ctypedef vector[Expr]                                   exprvec_t
ctypedef vector[OutputImageParam]                       outputimagevec_t
ctypedef vector[RVar]                                   rvarvec_t
ctypedef vector[string]                                 stringvec_t
ctypedef vector[Target]                                 targetvec_t
ctypedef vector[Type]                                   typevec_t
ctypedef unique_ptr[Module]                             moduleptr_t
ctypedef vector[pair[VarOrRVar, LoopAlignStrategy]]     varorpairvec_t
ctypedef vector[pair[RVar, Var]]                        rvarvarpairvec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Func # FORWARD!!
    
    cppclass Stage:
        Stage(Function, Definition, size_t, varvec_t&)
        Stage(Function, Definition, size_t, stringvec_t&)
        
        # StageSchedule get_schedule()
        
        string dump_argument_list()
        string name()
        
        Func rfactor(rvarvarpairvec_t)
        Func rfactor(RVar, Var)
        
        Stage& compute_with(LoopLevel, varorpairvec_t&)
        Stage& compute_with(LoopLevel, LoopAlignStrategy)
        Stage& compute_with(LoopLevel) # LoopAlignStrategy = Auto
        Stage& compute_with(Stage, LoopLevel, varorpairvec_t&)
        Stage& compute_with(Stage, LoopLevel, LoopAlignStrategy)
        Stage& compute_with(Stage, LoopLevel) # LoopAlignStrategy = Auto
        
        Stage& split(VarOrRVar, VarOrRVar, VarOrRVar, Expr, TailStrategy)
        Stage& split(VarOrRVar, VarOrRVar, VarOrRVar, Expr) # TailStrategy = Auto
        Stage& fuse(VarOrRVar, VarOrRVar, VarOrRVar)
        Stage& serial(VarOrRVar)
        Stage& parallel(VarOrRVar)
        Stage& vectorize(VarOrRVar)
        Stage& unroll(VarOrRVar)
        Stage& parallel(VarOrRVar, Expr, TailStrategy)
        Stage& parallel(VarOrRVar, Expr) # TailStrategy = Auto
        Stage& vectorize(VarOrRVar, Expr, TailStrategy)
        Stage& vectorize(VarOrRVar, Expr) # TailStrategy = Auto
        Stage& unroll(VarOrRVar, Expr, TailStrategy)
        Stage& unroll(VarOrRVar, Expr) # TailStrategy = Auto
        Stage& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy)
        Stage& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr) # TailStrategy = Auto
        Stage& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy)
        Stage& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr) # TailStrategy = Auto
        Stage& reorder(varorvec_t&)
        Stage& reorder(VarOrRVar, VarOrRVar, ...)
        
        Stage& rename(VarOrRVar, VarOrRVar)
        Stage  specialize(Expr)
        void   specialize_fail(string&)
        
        Stage& gpu_threads(VarOrRVar, DeviceAPI)
        Stage& gpu_threads(VarOrRVar) # DeviceAPI = Default_GPU
        Stage& gpu_threads(VarOrRVar, VarOrRVar, DeviceAPI)
        Stage& gpu_threads(VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        Stage& gpu_threads(VarOrRVar, VarOrRVar, VarOrRVar, DeviceAPI)
        Stage& gpu_threads(VarOrRVar, VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        Stage& gpu_lanes(VarOrRVar, DeviceAPI)
        Stage& gpu_lanes(VarOrRVar) # DeviceAPI = Default_GPU
        Stage& gpu_single_thread(DeviceAPI)
        Stage& gpu_single_thread() # DeviceAPI = Default_GPU
        Stage& gpu_blocks(VarOrRVar, DeviceAPI)
        Stage& gpu_blocks(VarOrRVar) # DeviceAPI = Default_GPU
        Stage& gpu_blocks(VarOrRVar, VarOrRVar, DeviceAPI)
        Stage& gpu_blocks(VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        Stage& gpu_blocks(VarOrRVar, VarOrRVar, VarOrRVar, DeviceAPI)
        Stage& gpu_blocks(VarOrRVar, VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        
        Stage& gpu(VarOrRVar, VarOrRVar, DeviceAPI)
        Stage& gpu(VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        Stage& gpu(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, DeviceAPI)
        Stage& gpu(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        Stage& gpu(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, DeviceAPI)
        Stage& gpu(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar) # DeviceAPI = Default_GPU
        
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, Expr, TailStrategy, DeviceAPI)
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        Stage& gpu_tile(VarOrRVar, VarOrRVar, Expr, TailStrategy, DeviceAPI)
        Stage& gpu_tile(VarOrRVar, VarOrRVar, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Stage& gpu_tile(VarOrRVar, VarOrRVar, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy, DeviceAPI)
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy, DeviceAPI)
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr, TailStrategy, DeviceAPI)
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr, TailStrategy, DeviceAPI)
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr, TailStrategy) # DeviceAPI = Default_GPU
        Stage& gpu_tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, Expr) # TailStrategy = Auto, DeviceAPI = Default_GPU
        
        Stage& allow_race_conditions()
        
        Stage& hexagon(VarOrRVar)
        Stage& hexagon()
        
        Stage& prefetch(Func&, VarOrRVar, Expr, PrefetchBoundStrategy)
        Stage& prefetch(Func&, VarOrRVar, Expr) # PrefetchBoundStrategy = GuardWithIf
        Stage& prefetch(Func&, VarOrRVar) # Expr offset = 1, PrefetchBoundStrategy = GuardWithIf
        Stage& prefetch(Parameter&, VarOrRVar, Expr, PrefetchBoundStrategy)
        Stage& prefetch(Parameter&, VarOrRVar, Expr) # PrefetchBoundStrategy = GuardWithIf
        Stage& prefetch(Parameter&, VarOrRVar) # Expr offset = 1, PrefetchBoundStrategy = GuardWithIf
        Stage& prefetch[T](T&, VarOrRVar, Expr, PrefetchBoundStrategy)
        Stage& prefetch[T](T&, VarOrRVar, Expr) # PrefetchBoundStrategy = GuardWithIf
        Stage& prefetch[T](T&, VarOrRVar) # Expr offset = 1, PrefetchBoundStrategy = GuardWithIf
        
        string& source_location()

ctypedef Stage ScheduleHandle
ctypedef Pipeline.RealizationArg RealizeArg
ctypedef vector[Func] funcvec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass FuncTupleElementRef
    
    cppclass FuncRef:
        FuncRef(Function, exprvec_t&, int, int)
        FuncRef(Function, exprvec_t&, int) # int = 0
        FuncRef(Function, exprvec_t&) # int = -1, int = 0
        FuncRef(Function, varvec_t&, int, int)
        FuncRef(Function, varvec_t&, int) # int = 0
        FuncRef(Function, varvec_t&) # int = -1, int = 0
        
        Stage operator=(Expr)
        # Stage operator=(Tuple&)
        Stage operator=(FuncRef&)
        
        # Stage operator+=(Expr)
        # Stage operator+=(Tuple&)
        # Stage operator+=(FuncRef&)
        # Stage operator-=(Expr)
        # Stage operator-=(Tuple&)
        # Stage operator-=(FuncRef&)
        # Stage operator*=(Expr)
        # Stage operator*=(Tuple&)
        # Stage operator*=(FuncRef&)
        # Stage operator/=(Expr)
        # Stage operator/=(Tuple&)
        # Stage operator/=(FuncRef&)
        
        # operator Func()
        FuncTupleElementRef operator[](int)
        size_t size()
        Function function()
    
    Expr min(FuncRef, FuncRef)
    Expr max(FuncRef, FuncRef)
    
    cppclass FuncTupleElementRef:
        FuncTupleElementRef(FuncRef&, exprvec_t&, int)
        Stage operator=(Expr)
        Stage operator=(FuncRef&)
        # Stage operator+=(Expr)
        # Stage operator-=(Expr)
        # Stage operator*=(Expr)
        # Stage operator/=(Expr)
        # operator Expr()
        Function function()
        int index()
    
    cppclass Func:
        
        Func(string&)
        Func()
        Func(Expr)
        Func(Function)
        # Func[T](Buffer[T]&)
        
        Realization realize(signed_sizevec_t, Target&)
        Realization realize(signed_sizevec_t) # target = default
        Realization realize(int, int, int, int, Target&)
        Realization realize(int, int, int, int) # target = default
        Realization realize(int, int, int, Target&)
        Realization realize(int, int, int) # target = default
        Realization realize(int, int, Target&)
        Realization realize(int, int) # target = default
        Realization realize(int, Target&)
        Realization realize(int) # target = default
        Realization realize(Target&)
        Realization realize() # target = default
        
        void realize(RealizeArg, Target&)
        void realize(RealizeArg) # target = default
        
        void infer_input_bounds(int, int, int, int)
        void infer_input_bounds(int, int, int)
        void infer_input_bounds(int, int)
        void infer_input_bounds(int)
        void infer_input_bounds()
        void infer_input_bounds(RealizeArg)
        
        void compile_to_bitcode(string&, argvec_t&, string&, Target&)
        void compile_to_bitcode(string&, argvec_t&, string&) # target = get_target_from_environment
        void compile_to_bitcode(string&, argvec_t&, Target&)
        void compile_to_bitcode(string&, argvec_t&) # target = get_target_from_environment
        void compile_to_llvm_assembly(string&, argvec_t&, string&, Target&)
        void compile_to_llvm_assembly(string&, argvec_t&, string&) # target = get_target_from_environment
        void compile_to_llvm_assembly(string&, argvec_t&, Target&)
        void compile_to_llvm_assembly(string&, argvec_t&) # target = get_target_from_environment
        void compile_to_object(string&, argvec_t&, string&, Target&)
        void compile_to_object(string&, argvec_t&, string&) # target = get_target_from_environment
        void compile_to_object(string&, argvec_t&, Target&)
        void compile_to_object(string&, argvec_t&) # target = get_target_from_environment
        void compile_to_header(string&, argvec_t&, string&, Target&)
        void compile_to_header(string&, argvec_t&, string&) # target = get_target_from_environment
        void compile_to_header(string&, argvec_t&) # target = get_target_from_environment
        void compile_to_assembly(string&, argvec_t&, string&, Target&)
        void compile_to_assembly(string&, argvec_t&, string&) # target = get_target_from_environment
        void compile_to_assembly(string&, argvec_t&, Target&)
        void compile_to_assembly(string&, argvec_t&) # target = get_target_from_environment
        void compile_to_c(string&, argvec_t&, string&, Target&)
        void compile_to_c(string&, argvec_t&, string&) # target = get_target_from_environment
        void compile_to_c(string&, argvec_t&) # target = get_target_from_environment
        void compile_to_lowered_stmt(string&, argvec_t&, StmtOutputFormat, Target&)
        void compile_to_lowered_stmt(string&, argvec_t&, StmtOutputFormat) # target = get_target_from_environment
        void compile_to_lowered_stmt(string&, argvec_t&) # target = get_target_from_environment
        void compile_to_python_extension(string&, argvec_t&, string&, Target&)
        void compile_to_python_extension(string&, argvec_t&, string&) # target = get_target_from_environment
        
        void print_loop_nest()
        
        void compile_to_file(string&, argvec_t&, string&, Target&)
        void compile_to_file(string&, argvec_t&, string&) # target = get_target_from_environment
        void compile_to_file(string&, argvec_t&) # target = get_target_from_environment
        void compile_to_static_library(string&, argvec_t&, string&, Target&)
        void compile_to_static_library(string&, argvec_t&, string&) # target = get_target_from_environment
        void compile_to_static_library(string&, argvec_t&) # target = get_target_from_environment
        
        void compile_to_multitarget_static_library(string&, argvec_t&, targetvec_t&)
        
        Module compile_to_module(argvec_t&, string&, Target&)
        Module compile_to_module(argvec_t&, string&) # target = get_target_from_environment
        Module compile_to_module(argvec_t&) # target = get_target_from_environment
        
        void compile_to(Outputs&, argvec_t&, string&, Target&)
        void compile_to(Outputs&, argvec_t&, string&) # target = get_target_from_environment
        
        void* compile_jit(Target&)
        void* compile_jit() # target = get_target_from_environment
        
        # void set_error_handler()
        # void set_custom_allocator()
        # void set_custom_do_task()
        # void set_custom_do_par_for()
        # void set_custom_trace()
        # void set_custom_print()
        
        JITHandlers& jit_handlers()
        
        void add_custom_lowering_pass[T](T*)
        void clear_custom_lowering_passes()
        customloweringpassvec_t& custom_lowering_passes()
        void debug_to_file(string&)
        
        string& name()
        varvec_t args()
        Expr value()
        # Tuple values()
        bint defined()
        exprvec_t& update_args(int)
        exprvec_t& update_args()
        Expr update_value(int)
        Expr update_value()
        # Tuple update_values(int)
        # Tuple update_values()
        rvarvec_t rvars(int)
        rvarvec_t rvars()
        
        bint has_update_definition()
        int num_update_definitions()
        bint is_extern()
        
        void define_extern(string&, extargvec_t&, Type, int, NameMangling, bint)
        void define_extern(string&, extargvec_t&, Type, int, NameMangling, DeviceAPI, bint)
        void define_extern(string&, extargvec_t&, Type, int, NameMangling, DeviceAPI)
        void define_extern(string&, extargvec_t&, Type, int, NameMangling)
        void define_extern(string&, extargvec_t&, Type, int)
        void define_extern(string&, extargvec_t&, typevec_t&, int, NameMangling, bint)
        void define_extern(string&, extargvec_t&, typevec_t&, int, NameMangling, DeviceAPI, bint)
        void define_extern(string&, extargvec_t&, typevec_t&, int, NameMangling, DeviceAPI)
        void define_extern(string&, extargvec_t&, typevec_t&, int, NameMangling)
        void define_extern(string&, extargvec_t&, typevec_t&, int)
        void define_extern(string&, extargvec_t&, Type, varvec_t&, NameMangling, bint)
        void define_extern(string&, extargvec_t&, Type, varvec_t&, NameMangling, DeviceAPI, bint)
        void define_extern(string&, extargvec_t&, Type, varvec_t&, NameMangling, DeviceAPI)
        void define_extern(string&, extargvec_t&, Type, varvec_t&, NameMangling)
        void define_extern(string&, extargvec_t&, Type, varvec_t&)
        void define_extern(string&, extargvec_t&, typevec_t&, varvec_t&, NameMangling, bint)
        void define_extern(string&, extargvec_t&, typevec_t&, varvec_t&, NameMangling, DeviceAPI, bint)
        void define_extern(string&, extargvec_t&, typevec_t&, varvec_t&, NameMangling, DeviceAPI)
        void define_extern(string&, extargvec_t&, typevec_t&, varvec_t&, NameMangling)
        void define_extern(string&, extargvec_t&, typevec_t&, varvec_t&)
        
        typevec_t& output_types()
        int outputs()
        string& extern_function_name()
        int dimensions()
        FuncRef operator()(varvec_t)
        FuncRef operator()(exprvec_t)
        
        Func func_in "in"(Func&)
        Func func_in "in"(funcvec_t&)
        Func func_in "in"()
        Func clone_in(Func&)
        Func clone_in(funcvec_t&)
        
        Func copy_to_device(DeviceAPI)
        Func copy_to_device()
        Func copy_to_host()
        
        Func& split(VarOrRVar, VarOrRVar, VarOrRVar, Expr, TailStrategy)
        Func& split(VarOrRVar, VarOrRVar, VarOrRVar, Expr) # TailStrategy = Auto
        Func& fuse(VarOrRVar, VarOrRVar, VarOrRVar)
        Func& serial(VarOrRVar)
        Func& parallel(VarOrRVar)
        Func& vectorize(VarOrRVar)
        Func& unroll(VarOrRVar)
        Func& parallel(VarOrRVar, Expr, TailStrategy)
        Func& parallel(VarOrRVar, Expr) # TailStrategy = Auto
        Func& vectorize(VarOrRVar, Expr, TailStrategy)
        Func& vectorize(VarOrRVar, Expr) # TailStrategy = Auto
        Func& unroll(VarOrRVar, Expr, TailStrategy)
        Func& unroll(VarOrRVar, Expr) # TailStrategy = Auto
        Func& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy)
        Func& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr) # TailStrategy = Auto
        Func& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr, TailStrategy)
        Func& tile(VarOrRVar, VarOrRVar, VarOrRVar, VarOrRVar, Expr, Expr) # TailStrategy = Auto
        Func& reorder(varorvec_t&)
        Func& reorder(VarOrRVar, VarOrRVar, ...)
        
        Func& bound(Var, Expr, Expr)
        Func& estimate(Var, Expr, Expr)
        Func& align_bounds(Var, Expr, Expr)
        Func& align_bounds(Var, Expr)
        Func& bound_extent(Var, Expr)
        
        Func& rename(VarOrRVar, VarOrRVar)
        Func& allow_race_conditions()
        
        Stage specialize(Expr)
        void specialize_fail(string&)
        
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
        
        Func& shader(Var, Var, Var, DeviceAPI)
        Func& glsl(Var, Var, Var)
        Func& hexagon(VarOrRVar)
        Func& hexagon()
        
        Func& prefetch(Func&, VarOrRVar, Expr, PrefetchBoundStrategy)
        Func& prefetch(Func&, VarOrRVar, Expr)
        Func& prefetch(Func&, VarOrRVar)
        Func& prefetch[T](T&, VarOrRVar, Expr, PrefetchBoundStrategy)
        Func& prefetch[T](T&, VarOrRVar, Expr)
        Func& prefetch[T](T&, VarOrRVar)
        
        Func& reorder_storage(varvec_t&)
        Func& reorder_storage(Var, Var)
        Func& align_storage(Var, Expr)
        Func& fold_storage(Var, Expr, bint)
        Func& fold_storage(Var, Expr)
        
        Func& compute_at(Func, Var)
        Func& compute_at(Func, RVar)
        Func& compute_at(LoopLevel)
        Func& compute_with(Stage, VarOrRVar, varorpairvec_t&)
        Func& compute_with(Stage, VarOrRVar, LoopAlignStrategy)
        Func& compute_with(Stage, VarOrRVar)
        Func& compute_with(LoopLevel, varorpairvec_t&)
        Func& compute_with(LoopLevel, LoopAlignStrategy)
        Func& compute_with(LoopLevel)
        Func& compute_root()
        Func& memoize()
        Func& store_at(Func, Var)
        Func& store_at(Func, RVar)
        Func& store_at(LoopLevel)
        Func& store_root()
        Func& compute_inline()
        
        Stage update(int)
        Stage update()
        
        # Func& store_in(MemoryType)
        
        Func& trace_loads()
        Func& trace_stores()
        Func& trace_realizations()
        Func& add_trace_tag(string&)
        
        Function function()
        # operator Stage()
        OutputImageParam output_buffer()
        outputimagevec_t output_buffers()
        # operator ExternFuncArgument()
        
        argvec_t infer_arguments()
        string source_location()



