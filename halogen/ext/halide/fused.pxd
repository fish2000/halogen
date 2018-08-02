
cimport cython
from libc.stdint cimport *
from libcpp.string cimport string

# ctypedef cython.fused_type(string, bytes) stringish_t
# ctypedef cython.fused_type(float, double, long double) floating_t

ctypedef fused stringish_t:
    str
    bytes
    string

ctypedef fused floating_t:
    float
    double
    long double
