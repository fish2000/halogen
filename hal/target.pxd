
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

cdef extern from "Halide.h" namespace "Halide":
    
    enum OS:
        OSUnknown
        Linux
        Windows
        OSX
        Android
        IOS
        NaCl
        QuRT
        NoOS
    
    enum Arch:
        ArchUnknown
        X86
        ARM
        PNaCl
        MIPS
        Hexagon
        POWERPC
    
    enum Feature:
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
    
    cdef cppclass Target:
        
        # members (defined as enums in header):
        OS os
        Arch arch
        int bits
        
        # ctypedef vector[Feature] featurevec_t
        
        # constructors:
        Target()
        Target(OS, Arch, int, vector[Feature])
        Target(string)
        
        # static methods:
        @staticmethod
        bint validate_target_string(string& s)
        
        # instance methods:
        void set_feature(Feature f, bint value)
        void set_features(vector[Feature] features_to_set, bint value)
        bint has_feature(Feature f)
        bint features_any_of(vector[Feature] test_features)
        bint features_all_of(vector[Feature] test_features)
        bint has_gpu_feature()
        Target with_feature(Feature f)
        Target without_feature(Feature f)
        
        # bool supports_type(Type const& t)
        # bool supports_device_api(DeviceAPI api)
        
        bint operator==(Target& other)
        bint operator!=(Target& other)
        string to_string()
        
        # int natural_vector_size(Type t)
        # int natural_vector_size[T]()
        int64_t maximum_buffer_size()
        bint supported()
    
    Target get_host_target()
    Target get_target_from_environment()
    Target get_jit_target_from_environment()
    
    # Target.Feature target_feature_for_device_api(DeviceAPI api)
