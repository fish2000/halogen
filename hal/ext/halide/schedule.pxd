
from libc.stdint cimport *
from libcpp.map cimport map as std_map
from libcpp.string cimport string
from libcpp.vector cimport vector

from device_api cimport DeviceAPI
from expr cimport Expr, ForType
from function cimport Function
from functionptr cimport FunctionContents
from parameter cimport Parameter
from varorrvar cimport VarOrRVar

ctypedef vector[string]     stringvec_t
ctypedef vector[uint8_t]    bytevec_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass LoopLevelContents:
        pass

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass TailStrategy:
        pass
    
    cppclass LoopAlignStrategy:
        pass
    
    cppclass PrefetchBoundStrategy:
        pass

cdef extern from "Halide.h" namespace "Halide::TailStrategy" nogil:
    
    cdef TailStrategy RoundUp
    cdef TailStrategy GuardWithIf
    cdef TailStrategy ShiftInwards
    cdef TailStrategy Auto
    
cdef extern from "Halide.h" namespace "Halide::LoopAlignStrategy" nogil:
    
    cdef LoopAlignStrategy AlignStart
    cdef LoopAlignStrategy AlignEnd
    cdef LoopAlignStrategy NoAlign
    cdef LoopAlignStrategy Auto
    
cdef extern from "Halide.h" namespace "Halide::PrefetchBoundStrategy" nogil:
    
    cdef PrefetchBoundStrategy Clamp
    cdef PrefetchBoundStrategy GuardWithIf
    cdef PrefetchBoundStrategy NonFaulting

ctypedef std_map[string, LoopAlignStrategy] loopalign_map_t

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Func
    
    cppclass LoopLevel:
        
        LoopLevel()
        LoopLevel(Function&, VarOrRVar, int)
        LoopLevel(Function&, VarOrRVar)
        LoopLevel(Func&, VarOrRVar, int)
        LoopLevel(Func&, VarOrRVar)
        
        int stage_index()
        
        @staticmethod
        LoopLevel inlined()
        @staticmethod
        LoopLevel root()
        
        void set(LoopLevel&)
        LoopLevel& lock()
        string func()
        VarOrRVar var()
        
        bint defined()
        bint is_inlined()
        bint is_root()
        
        string to_string()
        
        bint match(string&)
        bint match(LoopLevel&)
        bint operator==(LoopLevel&)
        bint operator!=(LoopLevel&)
    
    cppclass FuseLoopLevel:
        
        LoopLevel level
        loopalign_map_t align
        
        FuseLoopLevel()
        FuseLoopLevel(LoopLevel&, loopalign_map_t&)
        
ctypedef std_map[string, LoopLevel]     llevelmap_t

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass Split:
        
        string old_var
        string outer
        string inner
        Expr factor
        bint exact
        TailStrategy tail
        
        enum SplitType:
            SplitVar
            RenameVar
            FuseVars
            PurifyRVar
        
        SplitType split_type
        
        bint is_rename()
        bint is_split()
        bint is_fuse()
        bint is_purify()
    
    cppclass Dim:
        
        string var
        ForType for_type
        DeviceAPI device_api
        
        enum Type:
            PureVar
            PureRVar
            ImpureRVar
        
        Type dim_type
        
        bint is_pure()
        bint is_rvar()
        bint is_parallel()
    
    cppclass Bound:
        
        string var
        Expr bound_min "min"
        Expr extent
        Expr modulus
        Expr remainder
    
    cppclass StorageDim:
        
        string var
        Expr alignment
        Expr fold_factor
        bint fold_forward
    
    cppclass FusedPair:
        
        string func_1
        string func_2
        size_t stage_1
        size_t stage_2
        string var_name
        
        FusedPair()
        FusedPair(string&, size_t,
                  string&, size_t, string&)
        
        bint operator==(FusedPair&)
        bint  operator<(FusedPair&)
    
    cppclass PrefetchDirective:
        
        string name
        string var
        Expr offset
        PrefetchBoundStrategy strategy
        Parameter param
    
    