
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

cdef extern from "haldol/include/detail.hh" namespace "py":
    
    cppclass ref:
        
        ref()
        ref(bint)
        ref(ref&&)
        ref(object)
        ref& operator=(ref&&)
        ref& operator=(object)
        ref& set(object)
        ref& set(object, bint)
        
        ref& inc()
        ref& dec()
        ref& xinc()
        ref& xdec()
        ref& inc(size_t)
        ref& dec(size_t)
        ref& xinc(size_t)
        ref& xdec(size_t)
        ref& clear()
        
        object release()
        ref& reset()
        ref& reset(object)
        
        void swap(ref&)
        size_t hash()
        
        bint empty()
        bint truth()
        bint none()
        
        bint operator==(ref&)
        bint operator!=(ref&)
        bint  operator<(ref&)
        bint operator<=(ref&)
        bint  operator>(ref&)
        bint operator>=(ref&)
        
        string repr()
        string to_string()

