
cdef extern from "Halide.h" namespace "llvm" nogil:
    
    cppclass Module:
        # DO NOT IMPORT - name conflicts with Halide::Module
        pass
    
    cppclass Type:
        # DO NOT IMPORT - name conflicts with Halide::Type
        pass

# Import these prefixed typedefs instead:
ctypedef Module     LLVMModule
ctypedef Type       LLVMType