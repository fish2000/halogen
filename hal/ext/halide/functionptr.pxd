
from libc.stdint cimport *
from libcpp.vector cimport vector
from intrusiveptr cimport IntrusivePtr

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass FunctionGroup:
        pass
    
    cppclass FunctionContents:
        pass
    
    cppclass FunctionPtr:
        
        IntrusivePtr[FunctionGroup] strong
        FunctionGroup* weak
        int idx
        
        FunctionGroup* group()
        FunctionContents* get()
        FunctionContents& operator*()
        # FunctionContents* operator->()
        
        void weaken()
        bint defined()
        bint same_as(FunctionPtr&)
        bint operator<(FunctionPtr&)