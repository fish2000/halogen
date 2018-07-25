
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

from expr cimport Expr
from intrusiveptr cimport RefCount, IntrusivePtr
from runtime cimport halide_dimension_t, halide_type_t, halide_buffer_t, buffer_t
from types cimport Type

ctypedef vector[Expr]   exprvec_t
ctypedef vector[int]    intvec_t
    
cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass BufferContents:
        RefCount ref_count
        string name
    
ctypedef IntrusivePtr[BufferContents] buffercontents_ptr_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Buffer[T]:
        ctypedef T ElemType
        Buffer()
        # Buffer[T2](Buffer[T2]&)
        # Buffer[T2](Buffer[T2]&&)
        Buffer(Type, int, ...)
        Buffer(halide_buffer_t&, string&)
        Buffer(halide_buffer_t&)
        Buffer(buffer_t&, string&)
        Buffer(buffer_t&)
        Buffer(int, ...)
        Buffer(Type, intvec_t&, string&)
        Buffer(Type, intvec_t&)
        
        Buffer(T*, int, ...)
        Buffer(T*, intvec_t&, string&)
        Buffer(T*, intvec_t&)
        Buffer(Type, T*, intvec_t&, string&)
        Buffer(Type, T*, intvec_t&)
        Buffer(Type, T*, int, halide_dimension_t*, string&)
        Buffer(Type, T*, int, halide_dimension_t*)
        Buffer(T*, int, halide_dimension_t*, string&)
        Buffer(T*, int, halide_dimension_t*)
        
        @staticmethod
        Buffer[T] make_scalar(string&)
        @staticmethod
        Buffer[T] make_scalar()
        @staticmethod
        Buffer[T] make_scalar(Type, string&)
        @staticmethod
        Buffer[T] make_scalar(Type)
        
        @staticmethod
        Buffer[T] make_interleaved(int, int, int, string&)
        @staticmethod
        Buffer[T] make_interleaved(int, int, int)
        @staticmethod
        Buffer[T] make_interleaved(Type, int, int, int, string&)
        @staticmethod
        Buffer[T] make_interleaved(Type, int, int, int)
        @staticmethod
        Buffer[T] make_interleaved(T*, int, int, int, string&)
        @staticmethod
        Buffer[T] make_interleaved(T*, int, int, int)
        @staticmethod
        Buffer[T] make_interleaved(Type, T*, int, int, int, string&)
        @staticmethod
        Buffer[T] make_interleaved(Type, T*, int, int, int)
        
        @staticmethod
        Buffer[T] make_with_shape_of[T2](Buffer[T2])
        
        # @staticmethod
        # Buffer[T] make_with_shape_of[T2](RuntimeBuffer[T2]) # RUNTIME BUFFER
        
        # INSERT ALL THE FORWARDED Runtime::Buffer METHODS HERE
        
        void set_name(string&)
        string& name()
        
        bint same_as[T2](Buffer[T2]&)
        bint defined()
        
        # RuntimeBuffer* get() # RUNTIME BUFFER
        
        @staticmethod
        halide_type_t static_halide_type()
        
        @staticmethod
        bint can_convert_from[T2](Buffer[T2]&)
        
        Type type()
        Buffer[T2] buffer_as "as"[T2]()
        Buffer[T] copy()
        void copy_from[T2](Buffer[T2]&)
        
        # INSERT ALL THE operator() OVERLOADS HERE

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cdef Expr buffer_accessor(Buffer[void]&, exprvec_t&)

ctypedef vector[Buffer[void]] buffervec_t
ctypedef Buffer[void] VoidBuffer