
from libc.stdint cimport *

from expr cimport Expr

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass Dimension:
        
        Expr min()
        Expr extent()
        Expr max()
        Expr stride()
        Expr min_estimate()
        Expr extent_estimate()
        
        Dimension set_min(Expr)
        Dimension set_extent(Expr)
        Dimension set_stride(Expr)
        Dimension set_bounds(Expr, Expr)
        Dimension set_bounds_estimate(Expr, Expr)
        
        Dimension dim(int)
