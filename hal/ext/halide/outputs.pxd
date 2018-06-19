
from libcpp.string cimport string

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Outputs:
        
        string object_name
        string assembly_name
        string bitcode_name
        string llvm_assembly_name
        string c_header_name
        string c_source_name
        string stmt_name
        string stmt_html_name
        string static_library_name
        string python_extension_name
        string schedule_name
        
        Outputs() # default constructor
        
        Outputs object(string&)
        Outputs assembly(string&)
        Outputs bitcode(string&)
        Outputs llvm_assembly(string&)
        Outputs c_header(string&)
        Outputs c_source(string&)
        Outputs stmt(string&)
        Outputs stmt_html(string&)
        Outputs static_library(string&)
        Outputs python_extension(string&)
        Outputs schedule(string&)
