
cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cdef cppclass DeviceAPI:
        pass

cdef extern from "Halide.h" namespace "Halide::Internal::DeviceAPI" nogil:
    
    cdef DeviceAPI None
    cdef DeviceAPI Host
    cdef DeviceAPI Default_GPU
    cdef DeviceAPI CUDA
    cdef DeviceAPI OpenCL
    cdef DeviceAPI GLSL
    cdef DeviceAPI OpenGLCompute
    cdef DeviceAPI Metal
    cdef DeviceAPI Hexagon
