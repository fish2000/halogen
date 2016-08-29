
cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass IntrusivePtr[T]:
        T* get()
        
        IntrusivePtr()
        IntrusivePtr(T*)
        IntrusivePtr(IntrusivePtr[T]&)
        IntrusivePtr(IntrusivePtr[T]&&)
        IntrusivePtr[T]& operator=(IntrusivePtr[T]&)
        IntrusivePtr[T]& operator=(IntrusivePtr[T]&&)
        
        bint defined()
        bint same_as(IntrusivePtr[T]&)
        bint operator<(IntrusivePtr[T]&)
    