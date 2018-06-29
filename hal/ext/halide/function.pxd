
from libc.stdint cimport *
from libcpp.map cimport map as std_map
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.pair cimport pair

from buffer cimport Buffer
from definition cimport Definition
from device_api cimport DeviceAPI
from expr cimport Expr
from functionptr cimport FunctionContents, FunctionPtr
from intrusiveptr cimport IntrusivePtr
from parameter cimport Parameter
from target cimport Target
from type cimport Type

ctypedef vector[string]                     stringvec_t
ctypedef vector[Expr]                       exprvec_t
ctypedef vector[Type]                       typevec_t
ctypedef vector[Definition]                 definitionvec_t
ctypedef vector[Parameter]                  paramvec_t
ctypedef std_map[string, FunctionPtr]       wrappermap_t
ctypedef std_map[FunctionPtr, FunctionPtr]  functionptr_map_t

cdef extern from "Halide.h" namespace "Halide::ExternFuncArgument" nogil:
    
    cdef enum ArgType:
        UndefinedArg
        FuncArg
        BufferArg
        ExprArg
        ImageParamArg

ctypedef IntrusivePtr[FunctionContents] contents_ptr_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass ExternFuncArgument:
        
        ArgType arg_type
        FunctionPtr func
        Buffer[void] buffer
        Expr expr
        
        # YO DOGG: need constructors for:
        # - Halide::Buffer
        # x Halide::Expr
        # x Internal::IntrusivePtr<Internal::FunctionContents>
        # - Internal::Parameter (== Halide::ImageParam)
        
        # ExternFuncArgument[T](Buffer[T])
        ExternFuncArgument(FunctionPtr)
        # ExternFuncArgument(contents_ptr_t)
        ExternFuncArgument(Expr)
        ExternFuncArgument(int)
        ExternFuncArgument(float)
        ExternFuncArgument()
        
        bint is_func()
        bint is_expr()
        bint is_buffer()
        bint is_image_param()
        bint defined()

ctypedef vector[ExternFuncArgument] extargvec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cdef cppclass NameMangling:
        pass

cdef extern from "Halide.h" namespace "Halide::NameMangling" nogil:
    
    cdef NameMangling Default
    cdef NameMangling C
    cdef NameMangling CPlusPlus

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    # in the C++ header, this is a forward declaration:
    cppclass Call:
        pass
    
    cppclass Function:
        
        cppclass Compare:
            bint operator()(Function&, Function&)
        
        Function()
        Function(string&)
        Function(FunctionPtr&)
        
        FunctionPtr get_contents()
        
        void deep_copy(FunctionPtr, functionptr_map_t&)
        void deep_copy(string, FunctionPtr, functionptr_map_t&)
        
        void define(stringvec_t&, exprvec_t)
        void define_update(exprvec_t&, exprvec_t)
        
        # void accept(IRVisitor*)
        # void mutate(IRMutator2*)
        
        string& name()
        string& origin_name()
        Definition& definition()
        
        stringvec_t& args()
        int dimensions()
        int outputs()
        typevec_t& output_types()
        exprvec_t& values()
        
        bint has_pure_definition()
        bint is_pure()
        bint can_be_inlined()
        
        # FuncSchedule& schedule()
        paramvec_t output_buffers()
        # StageSchedule& update_schedule()
        # StageSchedule& update_schedule(int)
        
        Definition& update()
        Definition& update(int)
        definitionvec_t& updates()
        bint has_update_definition()
        bint has_extern_definition()
        bint extern_definition_uses_old_buffer_t()
        
        NameMangling extern_definition_name_mangling()
        Expr make_call_to_extern_definition(exprvec_t&, Target&)
        
        void define_extern(string&,
                           extargvec_t&, typevec_t&,
                           stringvec_t&, NameMangling,
                                         DeviceAPI,
                                         bint)
        
        extargvec_t& extern_arguments()
        string& extern_function_name()
        DeviceAPI extern_function_device_api()
        
        bint same_as(Function&)
        
        string& debug_file()
        # operator ExternFuncArgument()
        
        void trace_loads()
        void trace_stores()
        void trace_realizations()
        void add_trace_tag(string&)
        
        bint is_tracing_loads()
        bint is_tracing_stores()
        bint is_tracing_realizations()
        
        stringvec_t& get_trace_tags()
        void lock_loop_levels()
        void freeze()
        bint frozen()
        
        Function new_function_in_same_group(string&)
        void add_wrapper(string&, Function&)
        wrappermap_t& wrappers()
        
        Call* is_wrapper()
        
        Function& substitute_calls(functionptr_map_t&)
        Function& substitute_calls(Function&, Function&)
        
        bint is_pure_arg(string&)

ctypedef vector[Function]                   functionvec_t
ctypedef pair[functionvec_t, wrappermap_t]  deep_copy_result_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    deep_copy_result_t deep_copy(functionvec_t&, wrappermap_t&)
