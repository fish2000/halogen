
cimport cython
from libc.stdint cimport *
from libcpp.string cimport string

# ctypedef cython.fused_type(string, bytes) stringish_t
# ctypedef cython.fused_type(float, double, long double) floating_t

ctypedef fused 