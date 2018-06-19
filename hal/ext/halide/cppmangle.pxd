
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector
from type cimport Type
from target cimport Target
from function cimport extargvec_t

ctypedef vector[string] stringvec_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    # arguments to cplusplus_function_mangled_name() are:
    # - string& name,
    # - stringvec_t& namespaces,
    # - Type return_type,
    # - extargvec_t args,
    # - Target& target.
    # ... where: stringvec_t = vector[string],
    #            extargvec_t = vector[ExternFuncArgument].
    
    string cplusplus_function_mangled_name(string&, stringvec_t&,
                                           Type,    extargvec_t&,
                                           Target&)
