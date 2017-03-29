
from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.vector cimport vector

cdef extern from "numpy/ndarraytypes.h":
    pass

cdef extern from "numpy/arrayobject.h":
    
    cdef enum NPY_TYPES:
        NPY_BOOL
        NPY_BYTE
        NPY_UBYTE
        NPY_SHORT
        NPY_USHORT
        NPY_INT
        NPY_UINT
        NPY_LONG
        NPY_ULONG
        NPY_LONGLONG
        NPY_ULONGLONG
        NPY_FLOAT
        NPY_DOUBLE
        NPY_LONGDOUBLE
        NPY_CFLOAT
        NPY_CDOUBLE
        NPY_CLONGDOUBLE
        NPY_OBJECT
        NPY_STRING
        NPY_UNICODE
        NPY_VOID
        NPY_DATETIME
        NPY_TIMEDELTA
        NPY_HALF
        NPY_NTYPES
        NPY_NOTYPE
        NPY_CHAR
        NPY_USERDEF
        NPY_NTYPES_ABI_COMPATIBLE
    
    enum NPY_TYPECHAR:
        NPY_BOOLLTR
        NPY_BYTELTR
        NPY_UBYTELTR
        NPY_SHORTLTR
        NPY_USHORTLTR
        NPY_INTLTR
        NPY_UINTLTR
        NPY_LONGLTR
        NPY_ULONGLTR
        NPY_LONGLONGLTR
        NPY_ULONGLONGLTR
        NPY_HALFLTR
        NPY_FLOATLTR
        NPY_DOUBLELTR
        NPY_LONGDOUBLELTR
        NPY_CFLOATLTR
        NPY_CDOUBLELTR
        NPY_CLONGDOUBLELTR
        NPY_OBJECTLTR
        NPY_STRINGLTR
        NPY_STRINGLTR2
        NPY_UNICODELTR
        NPY_VOIDLTR
        NPY_DATETIMELTR
        NPY_TIMEDELTALTR
        NPY_CHARLTR
        NPY_INTPLTR
        NPY_UINTPLTR
        NPY_GENBOOLLTR
        NPY_SIGNEDLTR
        NPY_UNSIGNEDLTR
        NPY_FLOATINGLTR
        NPY_COMPLEXLTR
        
    enum:
        NPY_C_CONTIGUOUS
        NPY_F_CONTIGUOUS
        NPY_CONTIGUOUS
        NPY_FORTRAN
        NPY_OWNDATA
        NPY_FORCECAST
        NPY_ENSURECOPY
        NPY_ENSUREARRAY
        NPY_ELEMENTSTRIDES
        NPY_ALIGNED
        NPY_NOTSWAPPED
        NPY_WRITEABLE
        NPY_UPDATEIFCOPY
        NPY_ARR_HAS_DESCR
        NPY_BEHAVED
        NPY_BEHAVED_NS
        NPY_CARRAY
        NPY_CARRAY_RO
        NPY_FARRAY
        NPY_FARRAY_RO
        NPY_DEFAULT
        NPY_IN_ARRAY
        NPY_OUT_ARRAY
        NPY_INOUT_ARRAY
        NPY_IN_FARRAY
        NPY_OUT_FARRAY
        NPY_INOUT_FARRAY
        NPY_UPDATE_ALL
    
    cdef enum:
        NPY_MAXDIMS
    
    npy_intp NPY_MAX_ELSIZE


cdef extern from "haldol/include/typecode.hh" namespace "typecode" nogil:
    
    cdef NPY_TYPECHAR typechar(NPY_TYPES)
    cdef NPY_TYPECHAR typechar(unsigned int)
    
    # string "typechar_name" name (NPY_TYPES)
    # string "typechar_name" name (unsigned int)