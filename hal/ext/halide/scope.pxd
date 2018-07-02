
from libc.stdint cimport *
from libcpp.map cimport map as std_map
from libcpp.string cimport string

from expr cimport Expr

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass SmallStack[T]:
        
        SmallStack()
        void pop()
        void push(T&)
        T top()
        T& top_ref()
        bint empty()
    
    cppclass Scope[T]:
        
        Scope()
        void set_containing_scope(Scope[T]*)
        
        @staticmethod
        Scope[T]& empty_scope()
        
        T2 get[T2](string&)
        T2& ref[T2](string&)
        bint contains(string&)
        
        void push[T2](string&, T2&)
        void push[T2](string&)
        void pop(string&)
        
        ctypedef std_map[string, SmallStack[T]] stringstackmap_t
        
        cppclass const_iterator:
            
            const_iterator(stringstackmap_t&)
            const_iterator()
            bint operator!=(const_iterator&)
            void operator++()
            string& name()
            SmallStack[T]& stack()
            T& value()
        
        const_iterator cbegin()
        const_iterator cend()
        
        cppclass iterator:
            
            iterator(stringstackmap_t&)
            iterator()
            bint operator!=(iterator&)
            void operator++()
            string& name()
            SmallStack[T]& stack()
            T& value()
        
        iterator begin()
        iterator end()
        
        void swap(Scope[T]&)
    
    cppclass ScopedBinding[T]:
        
        Scope[T]* scope
        string name
        
        ScopedBinding(Scope[T]&, string&, T&)
        ScopedBinding(bint, Scope[T]&, string&, T&)
        
        ScopedBinding(Scope[T]&, string&) # T = void
