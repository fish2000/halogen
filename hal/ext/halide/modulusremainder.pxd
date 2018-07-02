
from libc.stdint cimport *

from expr cimport Expr
from scope cimport Scope

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass ModulusRemainder:
        
        ModulusRemainder()
        ModulusRemainder(int, int)
    
    ModulusRemainder modulus_remainder(Expr)
    ModulusRemainder modulus_remainder(Expr, Scope[ModulusRemainder]&)
    
    bint reduce_expr_modulo(Expr, int, int*)
    bint reduce_expr_modulo(Expr, int, int*, Scope[ModulusRemainder]&)
    
    void modulus_remainder_test()
    
    int64_t gcd(int64_t, int64_t)
    int64_t lcm(int64_t, int64_t)