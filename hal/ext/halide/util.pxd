
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

ctypedef vector[string] stringvec_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    # OS / environment:
    string make_entity_name(void*, string&, char)
    string get_env_variable(char*)
    string running_program_name()
    
    # unique names:
    string unique_name(char)
    string unique_name(string&)
    
    # string manipulation:
    bint starts_with(string&, string&) # string, prefix
    bint ends_with(string&, string&) # string, suffix
    string replace_all(string&, string&, string&) # subject, find, replace
    stringvec_t split_string(string&, string&)
    
    # filesystem manipulation:
    string extract_namespaces(string&, stringvec_t&)
    
    struct FileStat:
        uint64_t file_size
        uint32_t mod_time
        uint32_t uid
        uint32_t gid
        uint32_t mode
    
    string file_make_temp(string&, string&) # prefix, suffix
    string dir_make_temp()
    
    bint file_exists(string&)
    void assert_file_exists(string&)
    void assert_no_file_exists(string&)
    
    void file_unlink(string&)
    void ensure_no_file_exists(string&)
    void dir_rmdir(string&)
    FileStat file_stat(string&)
    
    cppclass TemporaryFile:
        TemporaryFile(string&, string&) # prefix, suffix
        string& pathname()
        void detach()
    
    # RAII template:
    cppclass ScopedValue[T]:
        T& var
        T old_value
        ScopedValue(T&)
        ScopedValue(T&, T)
        # operator T()
