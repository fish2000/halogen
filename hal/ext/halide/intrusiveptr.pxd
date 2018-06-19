
cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass RefCount:
        
        RefCount()
        
        int increment()
        int decrement()
        bint is_zero()
    
    RefCount& ref_count[T](T*)
    void        destroy[T](T*)
    
    cppclass IntrusivePtr[T]:
        
        IntrusivePtr()
        IntrusivePtr(T*)
        IntrusivePtr(IntrusivePtr[T]&)
        IntrusivePtr(IntrusivePtr[T]&&)
        IntrusivePtr[T]& operator=(IntrusivePtr[T]&)
        IntrusivePtr[T]& operator=(IntrusivePtr[T]&&)
        
        T* get()
        T& operator*()
        # T* operator->()
        
        bint defined()
        bint same_as(IntrusivePtr[T]&)
        bint operator<(IntrusivePtr[T]&)
    