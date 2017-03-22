
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

cdef extern from "haldol/include/terminal.hh" namespace "terminal" nogil:
    
    int terminal_width "width" ()
