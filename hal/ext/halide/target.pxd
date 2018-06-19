
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.memory cimport unique_ptr

from device_api cimport DeviceAPI
from type cimport Type

cdef extern from "Halide.h" namespace "Halide::Target" nogil:
    
    cdef cppclass OS:
        pass
    
    cdef cppclass Arch:
        pass
    
    cdef cppclass Feature:
        pass

cdef extern from "Halide.h" namespace "Halide::Target::OS" nogil:
    
    cdef OS OSUnknown
    cdef OS Linux
    cdef OS Windows
    cdef OS OSX
    cdef OS Android
    cdef OS IOS
    cdef OS QuRT
    cdef OS NoOS

cdef extern from "Halide.h" namespace "Halide::Target::Arch" nogil:
    
    cdef Arch ArchUnknown
    cdef Arch X86
    cdef Arch ARM
    cdef Arch MIPS
    cdef Arch Hexagon
    cdef Arch POWERPC

cdef extern from "Halide.h" namespace "Halide::Target::Feature" nogil:
    
    cdef Feature JIT
    cdef Feature Debug
    cdef Feature NoAsserts
    cdef Feature NoBoundsQuery
    cdef Feature SSE41
    cdef Feature AVX
    cdef Feature AVX2
    cdef Feature FMA
    cdef Feature FMA4
    cdef Feature F16C
    cdef Feature ARMv7s
    cdef Feature NoNEON
    cdef Feature VSX
    cdef Feature POWER_ARCH_2_07
    cdef Feature CUDA
    cdef Feature CUDACapability30
    cdef Feature CUDACapability32
    cdef Feature CUDACapability35
    cdef Feature CUDACapability50
    cdef Feature OpenCL
    cdef Feature CLDoubles
    cdef Feature OpenGL
    cdef Feature OpenGLCompute
    cdef Feature UserContext
    cdef Feature Matlab
    cdef Feature Profile
    cdef Feature NoRuntime
    cdef Feature Metal
    cdef Feature MinGW
    cdef Feature CPlusPlusMangling
    cdef Feature LargeBuffers
    cdef Feature HVX_64
    cdef Feature HVX_128
    cdef Feature HVX_v62
    cdef Feature HVX_shared_object
    cdef Feature FuzzFloatStores
    cdef Feature SoftFloatABI
    cdef Feature MSAN
    cdef Feature AVX512
    cdef Feature AVX512_KNL
    cdef Feature AVX512_Skylake
    cdef Feature AVX512_Cannonlake
    cdef Feature FeatureEnd

ctypedef vector[Feature] featurevec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Target:
        
        # members (defined as enums in header):
        OS os
        Arch arch
        int bits
        
        # constructors:
        Target()
        Target(OS, Arch, int, featurevec_t)
        Target(string)
        
        # static methods:
        @staticmethod
        bint validate_target_string(string&)
        
        # instance methods:
        void set_feature(Feature, bint)
        void set_features(featurevec_t, bint)
        bint has_feature(Feature)
        bint features_any_of(featurevec_t)
        bint features_all_of(featurevec_t)
        bint has_gpu_feature()
        Target with_feature(Feature)
        Target without_feature(Feature)
        
        bint supports_type(Type&)
        bint supports_device_api(DeviceAPI)
        
        bint operator==(Target&)
        bint operator!=(Target&)
        string to_string()
        
        int natural_vector_size(Type)
        # int natural_vector_size[T]()
        int64_t maximum_buffer_size()
        bint supported()
    
    Target get_host_target()
    Target get_target_from_environment()
    Target get_jit_target_from_environment()
    
    Feature target_feature_for_device_api(DeviceAPI)

ctypedef unique_ptr[Target] target_ptr_t
