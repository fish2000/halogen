
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from libcpp.pair cimport pair

from buffers cimport Buffer
from expr cimport Expr
from image cimport OutputImageParam

ctypedef vector[pair[Expr, Expr]] exprpairvec_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass RVar:
        
        RVar()
        RVar(string&)
        # RVar(ReductionDomain, int)
        
        string& name()
        # ReductionDomain domain()
        # operator Expr()
        
        Expr min()
        Expr extent()
    
    cppclass RDom:
        
        RDom()
        RDom(exprpairvec_t&)
        RDom(exprpairvec_t&, string)
        RDom(Expr, Expr, ...) # min, extent, args
        RDom(Buffer[void]&)
        RDom(OutputImageParam&)
        # RDom[T](Buffer[T]&)
        
        # RDom(ReductionDomain)
        # ReductionDomain domain()
        
        bint defined()
        bint same_as(RDom&)
        int dimensions()
        
        RVar operator[](int)
        # operator RVar()
        # operator Expr()
        
        void where(Expr)
        
        RVar x
        RVar y
        RVar z
        RVar w
