
from libc.stdint cimport *

cdef extern from "HalideRuntime.h":
    
    ctypedef enum halide_type_code_t:
        halide_type_int
        halide_type_uint
        halide_type_float
        halide_type_handle
    
    cdef struct halide_type_t:
        halide_type_code_t code
        uint8_t bits
        uint16_t lanes
    
    cdef enum halide_error_code_t:
        halide_error_code_success
        halide_error_code_generic_error
        halide_error_code_explicit_bounds_too_small
        halide_error_code_bad_elem_size
        halide_error_code_access_out_of_bounds
        halide_error_code_buffer_allocation_too_large
        halide_error_code_buffer_extents_too_large
        halide_error_code_constraints_make_required_region_smaller
        halide_error_code_constraint_violated
        halide_error_code_param_too_small
        halide_error_code_param_too_large
        halide_error_code_out_of_memory
        halide_error_code_buffer_argument_is_null
        halide_error_code_debug_to_file_failed
        halide_error_code_copy_to_host_failed
        halide_error_code_copy_to_device_failed
        halide_error_code_device_malloc_failed
        halide_error_code_device_sync_failed
        halide_error_code_device_free_failed
        halide_error_code_no_device_interface
        halide_error_code_matlab_init_failed
        halide_error_code_matlab_bad_param_type
        halide_error_code_internal_error
        halide_error_code_device_run_failed
        halide_error_code_unaligned_host_ptr
        halide_error_code_bad_fold
        halide_error_code_fold_factor_too_small
    
    ctypedef enum halide_target_feature_t:
        halide_target_feature_jit
        halide_target_feature_debug
        halide_target_feature_no_asserts
        halide_target_feature_no_bounds_query
        halide_target_feature_sse41
        halide_target_feature_avx
        halide_target_feature_avx2
        halide_target_feature_fma
        halide_target_feature_fma4
        halide_target_feature_f16c
        halide_target_feature_armv7s
        halide_target_feature_no_neon
        halide_target_feature_vsx
        halide_target_feature_power_arch_2_07
        halide_target_feature_cuda
        halide_target_feature_cuda_capability30
        halide_target_feature_cuda_capability32
        halide_target_feature_cuda_capability35
        halide_target_feature_cuda_capability50
        halide_target_feature_opencl
        halide_target_feature_cl_doubles
        halide_target_feature_opengl
        halide_target_feature_openglcompute
        halide_target_feature_renderscript
        halide_target_feature_user_context
        halide_target_feature_register_metadata
        halide_target_feature_matlab
        halide_target_feature_profile
        halide_target_feature_no_runtime
        halide_target_feature_metal
        halide_target_feature_mingw
        halide_target_feature_c_plus_plus_mangling
        halide_target_feature_large_buffers
        halide_target_feature_hvx_64
        halide_target_feature_hvx_128
        halide_target_feature_hvx_v62
        halide_target_feature_end
    
    ctypedef struct buffer_t:
        uint64_t dev
        uint8_t* host
        int32_t extent[4]
        int32_t stride[4]
        int32_t min[4]
        int32_t elem_size
        bint host_dirty
        bint dev_dirty
    
    # cdef struct halide_scalar_value_t:
    #     union u:
    #         bint b
    #         int8_t i8
    #         int16_t i16
    #         int32_t i32
    #         int64_t i64
    #         uint8_t u8
    #         uint16_t u16
    #         uint32_t u32
    #         uint64_t u64
    #         float f32
    #         double f64
    #         void* handle
    
    cdef enum halide_argument_kind_t:
        halide_argument_kind_input_scalar
        halide_argument_kind_input_buffer
        halide_argument_kind_output_buffer
    
    cdef struct halide_filter_argument_t:
        char* name
        int32_t kind
        int32_t dimensions
        halide_type_t type
        # halide_scalar_value_t* def
        # halide_scalar_value_t* min
        # halide_scalar_value_t* max
    
    cdef struct halide_filter_metadata_t:
        int32_t version
        int32_t num_arguments
        halide_filter_argument_t* arguments
        char* target
        char* name
    
    float halide_float16_bits_to_float(uint16_t)
    double halide_float16_bits_to_double(uint16_t)
    