
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from type cimport Type

cdef extern from "Halide.h" namespace "Halide::Target" nogil:
    
    # THIS IS NOT TOWARD
    
    ctypedef enum OS:
        OSUnknown
        Linux
        Windows
        OSX
        Android
        IOS
        NaCl
        QuRT
        NoOS
    
    ctypedef enum Arch:
        ArchUnknown
        X86
        ARM
        PNaCl
        MIPS
        Hexagon
        POWERPC
    
    ctypedef enum Feature:
        JIT
        Debug
        NoAsserts
        NoBoundsQuery
        SSE41
        AVX
        AVX2
        FMA
        FMA4
        F16C
        ARMv7s
        NoNEON
        VSX
        POWER_ARCH_2_07
        CUDA
        CUDACapability30
        CUDACapability32
        CUDACapability35
        CUDACapability50
        OpenCL
        CLDoubles
        OpenGL
        OpenGLCompute
        Renderscript
        UserContext
        RegisterMetadata
        Matlab
        Profile
        NoRuntime
        Metal
        MinGW
        CPlusPlusMangling
        LargeBuffers
        HVX_64
        HVX_128
        HVX_v62
        FeatureEnd

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
        bint validate_target_string(string& s)
        
        # instance methods:
        void set_feature(Feature f, bint value)
        void set_features(featurevec_t features_to_set, bint value)
        bint has_feature(Feature f)
        bint features_any_of(featurevec_t test_features)
        bint features_all_of(featurevec_t test_features)
        bint has_gpu_feature()
        Target with_feature(Feature f)
        Target without_feature(Feature f)
        
        bint supports_type(Type&)
        # bint supports_device_api(DeviceAPI api)
        
        bint operator==(Target& other)
        bint operator!=(Target& other)
        string to_string()
        
        int natural_vector_size(Type)
        # int natural_vector_size[T]()
        int64_t maximum_buffer_size()
        bint supported()
    
    Target get_host_target()
    Target get_target_from_environment()
    Target get_jit_target_from_environment()
    
    # Target.Feature target_feature_for_device_api(DeviceAPI api)
