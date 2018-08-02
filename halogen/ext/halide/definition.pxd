
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

from expr cimport Expr
from functionptr cimport FunctionContents
from intrusiveptr cimport IntrusivePtr
from target cimport Target

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass DefinitionContents:
        pass
        
    cppclass Specialization


ctypedef vector[Expr]                       exprvec_t
ctypedef vector[Specialization]             specialvec_t
ctypedef IntrusivePtr[DefinitionContents]   DefinitionContentsPtr

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass Definition:
        # PRIVATE:
        # DefinitionContentsPtr contents
        
        Definition()
        Definition(DefinitionContentsPtr&)
        # Definition(exprvec_t, exprvec_t, ReductionDomain&, bint)
        Definition get_copy()
        
        bint same_as(Definition&)
        bint defined()
        bint is_init()
        
        # void accept(IRVisitor*)
        # void mutate(IRMutator2*)
        
        exprvec_t& args()
        exprvec_t& values()
        Expr& predicate()
        exprvec_t split_predicate()
        # StageSchedule& schedule()
        
        specialvec_t& specializations()
        Specialization& add_specialization(Expr)
        string source_location()
    
    cppclass Specialization:
        Expr condition
        Definition definition
        string failure_message
