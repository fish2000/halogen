
from libc.stdint cimport *
from libcpp.string cimport string

from intrusiveptr cimport RefCount, IntrusivePtr
from type cimport Type

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cdef cppclass IRNodeType:
        pass

cdef extern from "Halide.h" namespace "Halide::Internal::IRNodeType" nogil:
    
    cdef IRNodeType IntImmType      "IntImm"
    cdef IRNodeType UIntImmType     "UIntImm"
    cdef IRNodeType FloatImmType    "FloatImm"
    cdef IRNodeType StringImmType   "StringImm"
    cdef IRNodeType Cast
    cdef IRNodeType Variable
    cdef IRNodeType Add
    cdef IRNodeType Sub
    cdef IRNodeType Mul
    cdef IRNodeType Div
    cdef IRNodeType Mod
    cdef IRNodeType Min
    cdef IRNodeType Max
    cdef IRNodeType EQ
    cdef IRNodeType NE
    cdef IRNodeType LT
    cdef IRNodeType LE
    cdef IRNodeType GT
    cdef IRNodeType GE
    cdef IRNodeType And
    cdef IRNodeType Or
    cdef IRNodeType Not
    cdef IRNodeType Select
    cdef IRNodeType Load
    cdef IRNodeType Ramp
    cdef IRNodeType Broadcast
    cdef IRNodeType Call
    cdef IRNodeType Let
    cdef IRNodeType LetStmt
    cdef IRNodeType AssertStmt
    cdef IRNodeType ProducerConsumer
    cdef IRNodeType For
    cdef IRNodeType Store
    cdef IRNodeType Provide
    cdef IRNodeType Allocate
    cdef IRNodeType Free
    cdef IRNodeType Realize
    cdef IRNodeType Block
    cdef IRNodeType IfThenElse
    cdef IRNodeType Evaluate
    cdef IRNodeType Shuffle
    cdef IRNodeType Prefetch

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass IRNode:
        RefCount ref_count
        IRNodeType node_type
        IRNode(IRNodeType)
        # void accept(IRVisitor*)
    
    cppclass BaseStmtNode(IRNode):
        BaseStmtNode(IRNodeType)
    
    cppclass BaseExprNode(IRNode):
        BaseExprNode(IRNodeType)
    
    cppclass StmtNode[T](BaseStmtNode):
        BaseStmtNode()
    
    cppclass ExprNode[T](BaseExprNode):
        BaseExprNode()
    
    cppclass IRHandle(IntrusivePtr[IRNode]):
        IRHandle()
        IRHandle(IRNode*)
        T* as_type "as"[T]()
    
    cdef cppclass IntImm
    cdef cppclass IntImm(ExprNode[IntImm]):
        int64_t value
        @staticmethod
        IntImm* make(Type, int64_t)
    
    cdef cppclass UIntImm
    cdef cppclass UIntImm(ExprNode[UIntImm]):
        uint64_t value
        @staticmethod
        UIntImm* make(Type, uint64_t)
    
    cdef cppclass FloatImm
    cdef cppclass FloatImm(ExprNode[FloatImm]):
        double value
        @staticmethod
        FloatImm* make(Type, double)
    
    cdef cppclass StringImm
    cdef cppclass StringImm(ExprNode[StringImm]):
        string value
        @staticmethod
        StringImm* make(Type, string&)

cdef extern from "Halide.h" namespace "Halide" nogil:
    
    cppclass Expr(IRHandle):
        
        Expr()
        Expr(BaseExprNode*)
        
        Expr(int8_t)
        Expr(int16_t)
        Expr(int32_t)
        Expr(int64_t)
        Expr(uint8_t)
        Expr(uint16_t)
        Expr(uint32_t)
        Expr(uint64_t)
        Expr(float16_t)
        Expr(float)
        Expr(double)
        Expr(string&)
        
        Type type()
    
    cppclass ExprCompare:
        bint operator()(Expr&, Expr&)
    
    # cdef DeviceAPI all_device_apis[] = 
    
    cppclass MemoryType:
        pass
    
cdef extern from "Halide.h" namespace "Halide::MemoryType" nogil:
    
    cdef MemoryType Auto
    cdef MemoryType Heap
    cdef MemoryType Stack
    cdef MemoryType Register
    cdef MemoryType GPUShared

cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass ForType:
        pass
    
cdef extern from "Halide.h" namespace "Halide::Internal::ForType" nogil:
    
    cdef ForType Serial
    cdef ForType Parallel
    cdef ForType Vectorized
    cdef ForType Unrolled
    cdef ForType GPUBlock
    cdef ForType GPUThread
    cdef ForType GPULanes
    
cdef extern from "Halide.h" namespace "Halide::Internal" nogil:
    
    cppclass Stmt(IRHandle):
        
        Stmt()
        Stmt(BaseStmtNode*)
        
        cppclass Compare:
            bint operator()(Stmt&, Stmt&)
