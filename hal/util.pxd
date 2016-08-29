
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

ctypedef vector[string] stringvec_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    string unique_name(string&)
    stringvec_t split_string(string&, string&)
    string extract_namespaces(string&, stringvec_t&)
    
    struct FileStat:
        uint64_t file_size
        uint32_t mod_time
        uint32_t uid
        uint32_t gid
        uint32_t mode

