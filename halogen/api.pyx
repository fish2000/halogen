#!/usr/bin/env cython
# distutils: language = c++
from array import array

import cython
cimport cython
from cython.operator cimport dereference as deref
from cython.operator cimport preincrement as incr
# from cython.operator cimport address as addressof

from libc.stdint cimport *
# from libcpp.cast cimport static_cast
from libcpp.string cimport string
from libcpp.memory cimport unique_ptr

from cpython.bool cimport PyBool_FromLong
from cpython.int cimport PyInt_FromLong, PyInt_AsLong
# from cpython.long cimport PyLong_AsLong
from cpython.mapping cimport PyMapping_Check
from cpython.object cimport PyObject_IsTrue

# from ext.halide.function cimport ExternFuncArgument as HalExternFuncArgument
# from ext.halide.function cimport NameMangling as HalNameMangling
from ext.halide.function cimport Function as HalFunction

from ext.halide.outputs cimport Outputs as HalOutputs
from ext.halide.module cimport Module as HalModule
from ext.halide.module cimport LinkageType, LoweredFunc
# from ext.halide.module cimport External as Linkage_External
# from ext.halide.module cimport ExternalPlusMetadata as Linkage_ExternalPlusMetadata
from ext.halide.module cimport Internal as Linkage_Internal
from ext.halide.module cimport funcvec_t
from ext.halide.module cimport modulevec_t
from ext.halide.module cimport link_modules as halide_link_modules
from ext.halide.module cimport halide_compile_standalone_runtime_for_path
from ext.halide.module cimport halide_compile_standalone_runtime_with_outputs

from ext.halide.generator cimport GeneratorBase
from ext.halide.generator cimport GeneratorRegistry
from ext.halide.generator cimport GeneratorContext
from ext.halide.generator cimport GeneratorParamsMap
from ext.halide.generator cimport StringOrLoopLevel
from ext.halide.generator cimport stringmap_t
from ext.halide.generator cimport base_ptr_t
from ext.halide.generator cimport generator_registry_get as halide_generator_registry_get
from ext.halide.generator cimport generator_registry_create as halide_generator_registry_create

from ext.halide.types cimport Type as HalType
from ext.halide.types cimport Int as HalType_Int
from ext.halide.types cimport UInt as HalType_UInt
from ext.halide.types cimport Float as HalType_Float
from ext.halide.types cimport Bool as HalType_Bool
from ext.halide.types cimport Handle as HalType_Handle
from ext.halide.types cimport halide_type_to_c_source
from ext.halide.types cimport halide_type_to_c_type
from ext.halide.types cimport halide_type_to_enum_string

from ext.halide.target cimport Target as HalTarget
from ext.halide.target cimport OS, Arch, Feature
from ext.halide.target cimport Windows as OS_Windows
from ext.halide.target cimport MinGW as Feature_MinGW
# from ext.halide.device_api cimport DeviceAPI

from ext.halide.target cimport target_ptr_t
from ext.halide.target cimport get_host_target as halide_get_host_target
from ext.halide.target cimport get_target_from_environment as halide_get_target_from_environment
from ext.halide.target cimport get_jit_target_from_environment as halide_get_jit_target_from_environment
cimport ext.halide.target as target

from ext.halide.util cimport stringvec_t
from ext.halide.util cimport extract_namespaces as halide_extract_namespaces
from ext.halide.util cimport running_program_name as halide_running_program_name

from ext.halide.func cimport Stage as HalStage
from ext.halide.func cimport Func as HalFunc

from ext.halide.buffers cimport Buffer
from ext.halide.buffers cimport buffervec_t


cdef inline bytes u8encode(object source):
    return bytes(source, encoding='UTF-8')

cpdef bytes u8bytes(object source):
    """ Custom version of u8bytes(…) for use in Cython extensions: """
    if type(source) is bytes:
        return source
    elif type(source) is str:
        return u8encode(source)
    elif type(source) is unicode:
        return u8encode(source)
    elif type(source) is int:
        return u8encode(str(source))
    elif type(source) is long:
        return u8encode(str(source))
    elif type(source) is float:
        return u8encode(str(source))
    elif type(source) is bool:
        return source and b'True' or b'False'
    elif type(source) is type(None):
        return b'None'
    elif type(source) is array:
        return bytes(source)
    elif type(source) is memoryview:
        return bytes(source)
    if hasattr(source, '__fspath__'):
        return u8encode(source.__fspath__())
    elif hasattr(source, '__str__'):
        return u8encode(str(source))
    elif hasattr(source, '__bytes__'):
        return bytes(source)
    elif hasattr(source, '__unicode__'):
        return u8encode(unicode(source))
    elif hasattr(source, '__bool__'):
        return bool(source) and b'True' or b'False'
    return bytes(source)

cpdef str u8str(object source):
    """ Custom version of u8str(…) for use in Cython extensions: """
    return u8bytes(source).decode('UTF-8')

def stringify(object instance not None,
              object fields not None):
    """ Custom version of stringify(instance, fields) for use in Cython extensions: """
    field_dict = {}
    for field in fields:
        field_value = getattr(instance, field, b"")
        if field_value:
            field_dict.update({ field : field_value })
    field_dict_items = []
    for k, v in field_dict.items():
        field_dict_items.append(b'''%s="%s"''' % (u8bytes(k),
                                                  u8bytes(v)))
    return b"%s(%s) @ %s" % (u8encode(type(instance).__name__),
                             b", ".join(field_dict_items),
                             u8encode(hex(id(instance))))


@cython.freelist(32)
cdef class Type:
    """ Cython wrapper class for Halide::Type """
    
    cdef:
        HalType __this__
    
    @staticmethod
    def fromother(Type other not None):
        out = Type()
        out.__this__ = HalType(other.__this__)
        return out
    
    def __cinit__(self, Type other=None, **kwargs):
        # FIRST: examine `other` argument, looking for an existing Type object,
        # from which we can copy-construct:
        if other is not None:
            if type(other) is type(self):
                self.__this__ = HalType(other.__this__)
                return
        # NEXT, IF THAT DIDN’T WORK: check **kwargs for one of either:
        # 'code', 'bits', or 'lanes' -- if any one of these is specified,
        # try to use it to default-ish-construct a new Type with the named
        # specification. We do it like this because Halide::Type implements these
        # `with_whatever()` single-argument static construction helper methods:
        if 'code' in kwargs:
            self.__this__ = self.__this__.with_code(kwargs.get('code'))
        elif 'bits' in kwargs:
            self.__this__ = self.__this__.with_bits(<uint8_t>kwargs.get('bits'))
        elif 'lanes' in kwargs:
            self.__this__ = self.__this__.with_lanes(<uint16_t>kwargs.get('lanes'))
        else:
            # default to “uint8_t”:
            self.__this__ = HalType_UInt(8, 1)
    
    def code(self):
        return self.__this__.code()
    
    def bytes(self):
        return self.__this__.bytes()
    
    def bits(self):
        return self.__this__.bits()
    
    def lanes(self):
        return self.__this__.lanes()
    
    def with_code(self, code):
        out = Type()
        out.__this__ = self.__this__.with_code(code)
        return out
    
    def with_bits(self, bits):
        out = Type()
        out.__this__ = self.__this__.with_bits(<uint8_t>bits)
        return out
    
    def with_lanes(self, lanes):
        out = Type()
        out.__this__ = self.__this__.with_lanes(<uint16_t>lanes)
        return out
    
    def is_bool(self):
        return self.__this__.is_bool()
    
    def is_vector(self):
        return self.__this__.is_vector()
    
    def is_scalar(self):
        return self.__this__.is_scalar()
    
    def is_float(self):
        return self.__this__.is_float()
    
    def is_int(self):
        return self.__this__.is_int()
    
    def is_uint(self):
        return self.__this__.is_uint()
    
    def is_handle(self):
        return self.__this__.is_handle()
    
    def same_handle_type(self, Type other not None):
        return self.__this__.same_handle_type(other.__this__)
    
    def element_of(self):
        out = Type()
        out.__this__ = self.__this__.element_of()
        return out
    
    def can_represent(self, other):
        if type(other) is type(self):
            return self.can_represent_type(other)
        elif type(other) is float:
            return self.can_represent_float(float(other))
        elif type(other) is int:
            return self.can_represent_long(long(other))
        elif type(other) is long:
            return self.can_represent_long(long(other))
        return False
    
    cpdef object can_represent_type(Type self, Type other):
        return self.__this__.can_represent(other.__this__)
    
    cpdef object can_represent_float(Type self, float other):
        return self.__this__.can_represent(<double>other)
    
    cpdef object can_represent_long(Type self, long other):
        return self.__this__.can_represent(<int64_t>other)
    
    def repr_c_source(self):
        try:
            return halide_type_to_c_source(self.__this__)
        except IndexError:
            return b"Halide::type_sink<void>"
    
    def repr_c_type(self):
        try:
            return halide_type_to_c_type(self.__this__)
        except IndexError:
            return b"void"
    
    def repr_enum_string(self):
        try:
            return halide_type_to_enum_string(self.__this__)
        except IndexError:
            return b"void"
    
    def to_string(Type self not None):
        try:
            return halide_type_to_c_type(self.__this__)
        except IndexError:
            return b"void"
    
    def __repr__(self):
        try:
            c_source = <bytes>halide_type_to_c_source(self.__this__)
        except IndexError:
            c_source = b"Halide::type_sink<void>"
        return "<%s @ %s>" % (c_source.decode('UTF-8'),
                              hex(id(self)))
    
    def __str__(self):
        try:
            c_type = <bytes>halide_type_to_c_type(self.__this__)
        except IndexError:
            c_type = b"void"
        return c_type.decode('UTF-8')
    
    def __bytes__(self):
        try:
            c_type = <bytes>halide_type_to_c_type(self.__this__)
        except IndexError:
            c_type = b"void"
        return c_type
    
    @staticmethod
    def Int(int bits, int lanes=1):
        out = Type()
        out.__this__ = HalType_Int(bits, lanes)
        return out
    
    @staticmethod
    def UInt(int bits, int lanes=1):
        out = Type()
        out.__this__ = HalType_UInt(bits, lanes)
        return out
    
    @staticmethod
    def Float(int bits, int lanes=1):
        out = Type()
        out.__this__ = HalType_Float(bits, lanes)
        return out
    
    @staticmethod
    def Bool(int lanes=1):
        out = Type()
        out.__this__ = HalType_Bool(lanes)
        return out
    
    @staticmethod
    def Handle(int lanes=1):
        out = Type()
        out.__this__ = HalType_Handle(lanes, NULL)
        return out


@cython.freelist(32)
cdef class Target:
    """ Cython wrapper class for Halide::Target """
    
    cdef:
        HalTarget __this__
    
    @staticmethod
    def validate_target_string(object target_string not None):
        return HalTarget.validate_target_string(<string>u8bytes(target_string))
    
    def __cinit__(self, *args, **kwargs):
        cdef string target_string = b'host'
        if 'target_string' in kwargs:
            target_string = <string>u8bytes(kwargs.get('target_string', target_string))
        elif len(args) > 0:
            target_string = <string>u8bytes(args[0])
        if not HalTarget.validate_target_string(target_string):
            raise ValueError("invalid target string: %s" % u8str(target_string))
        self.__this__ = HalTarget(target_string)
        # INSERT FEATURE CHECK HERE
    
    @property
    def os(self):
        return PyInt_FromLong(<long>(self.__this__.os))
    
    @os.setter
    def os(self, value not None):
        self.__this__.os = <OS>PyInt_AsLong(int(value))
    
    @property
    def arch(self):
        return PyInt_FromLong(<long>(self.__this__.arch))
    
    @arch.setter
    def arch(self, value not None):
        self.__this__.arch = <Arch>PyInt_AsLong(int(value))
    
    @property
    def bits(self):
        return PyInt_FromLong(self.__this__.bits)
    
    @bits.setter
    def bits(self, value not None):
        self.__this__.bits = <int>PyInt_AsLong(int(value))
    
    def has_gpu_feature(self):
        return self.__this__.has_gpu_feature()
    
    def has_feature(self, feature):
        return self.__this__.has_feature(<Feature>PyInt_AsLong(int(feature)))
    
    def includes_halide_runtime(self):
        try:
            return self.to_string().decode('UTF-8').lower().index('no_runtime') < 0
        except ValueError:
            return True
    
    def to_string(self):
        return self.__this__.to_string()
    
    def maximum_buffer_size(self):
        return self.__this__.maximum_buffer_size()
    
    def supported(self):
        return self.__this__.supported()
    
    def supports_type(self, Type t not None):
        return self.__this__.supports_type(t.__this__)
    
    def natural_vector_size(self, Type t not None):
        return self.__this__.natural_vector_size(t.__this__)
    
    def __str__(self):
        return self.__this__.to_string().decode('UTF-8')
    
    def __bytes__(self):
        return self.__this__.to_string()
    
    def __repr__(self):
        return stringify(self, ('os', 'arch', 'bits')).decode('UTF-8')
    
    def __richcmp__(self, Target other not None,
                             int op):
        if op == 2: # ==
            return bool(<HalTarget>self.__this__ == <HalTarget>other.__this__)
        elif op == 3: # !=
            return bool(<HalTarget>self.__this__ != <HalTarget>other.__this__)
        return False
    
    @staticmethod
    def host_target():
        out = Target()
        with nogil:
            out.__this__ = halide_get_host_target()
        return out
    
    @staticmethod
    def target_from_environment():
        out = Target()
        with nogil:
            out.__this__ = halide_get_target_from_environment()
        return out
    
    @staticmethod
    def jit_target_from_environment():
        out = Target()
        with nogil:
            out.__this__ = halide_get_jit_target_from_environment()
        return out


@cython.freelist(32)
cdef class Outputs:
    """ Cython wrapper class for Halide::Outputs """
    
    cdef:
        HalOutputs __this__
    
    @classmethod
    def check(cls, instance):
        return getattr(instance, '__class__', None) is cls
    
    def __cinit__(self, *args, **kwargs):
        for arg in args:
            if type(arg) is type(self):
                self.__this__ = self.__this__.object(arg.object_name) \
                                             .assembly(arg.assembly_name) \
                                             .bitcode(arg.bitcode_name) \
                                             .llvm_assembly(arg.llvm_assembly_name) \
                                             .c_header(arg.c_header_name) \
                                             .c_source(arg.c_source_name) \
                                             .python_extension(arg.python_extension_name) \
                                             .stmt(arg.stmt_name) \
                                             .stmt_html(arg.stmt_html_name) \
                                             .static_library(arg.static_library_name) \
                                             .schedule(arg.schedule_name)
                return
        
        object_name = kwargs.pop('object_name', '')
        assembly_name = kwargs.pop('assembly_name', '')
        bitcode_name = kwargs.pop('bitcode_name', '')
        llvm_assembly_name = kwargs.pop('llvm_assembly_name', '')
        c_header_name = kwargs.pop('c_header_name', '')
        c_source_name = kwargs.pop('c_source_name', '')
        python_extension_name = kwargs.pop('python_extension_name', '')
        stmt_name = kwargs.pop('stmt_name', '')
        stmt_html_name = kwargs.pop('stmt_html_name', '')
        static_library_name = kwargs.pop('static_library_name', '')
        schedule_name = kwargs.pop('schedule_name', '')
        
        self.__this__.object_name = <string>u8bytes(object_name)
        self.__this__.assembly_name = <string>u8bytes(assembly_name)
        self.__this__.bitcode_name = <string>u8bytes(bitcode_name)
        self.__this__.llvm_assembly_name = <string>u8bytes(llvm_assembly_name)
        self.__this__.c_header_name = <string>u8bytes(c_header_name)
        self.__this__.c_source_name = <string>u8bytes(c_source_name)
        self.__this__.python_extension_name = <string>u8bytes(python_extension_name)
        self.__this__.stmt_name = <string>u8bytes(stmt_name)
        self.__this__.stmt_html_name = <string>u8bytes(stmt_html_name)
        self.__this__.static_library_name = <string>u8bytes(static_library_name)
        self.__this__.schedule_name = <string>u8bytes(schedule_name)
    
    @property
    def object_name(self):
        return <string>self.__this__.object_name
    @object_name.setter
    def object_name(self, object value not None):
        self.__this__.object_name = <string>u8bytes(value)
    
    @property
    def assembly_name(self):
        return <string>self.__this__.assembly_name
    @assembly_name.setter
    def assembly_name(self, object value not None):
        self.__this__.assembly_name = <string>u8bytes(value)
    
    @property
    def bitcode_name(self):
        return <string>self.__this__.bitcode_name
    @bitcode_name.setter
    def bitcode_name(self, object value not None):
        self.__this__.bitcode_name = <string>u8bytes(value)
    
    @property
    def llvm_assembly_name(self):
        return <string>self.__this__.llvm_assembly_name
    @llvm_assembly_name.setter
    def llvm_assembly_name(self, object value not None):
        self.__this__.llvm_assembly_name = <string>u8bytes(value)
    
    @property
    def c_header_name(self):
        return <string>self.__this__.c_header_name
    @c_header_name.setter
    def c_header_name(self, object value not None):
        self.__this__.c_header_name = <string>u8bytes(value)
    
    @property
    def c_source_name(self):
        return <string>self.__this__.c_source_name
    @c_source_name.setter
    def c_source_name(self, object value not None):
        self.__this__.c_source_name = <string>u8bytes(value)
    
    @property
    def python_extension_name(self):
        return <string>self.__this__.python_extension_name
    @python_extension_name.setter
    def python_extension_name(self, object value not None):
        self.__this__.python_extension_name = <string>u8bytes(value)
    
    @property
    def stmt_name(self):
        return <string>self.__this__.stmt_name
    @stmt_name.setter
    def stmt_name(self, object value not None):
        self.__this__.stmt_name = <string>u8bytes(value)
    
    @property
    def stmt_html_name(self):
        return <string>self.__this__.stmt_html_name
    @stmt_html_name.setter
    def stmt_html_name(self, object value not None):
        self.__this__.stmt_html_name = <string>u8bytes(value)
    
    @property
    def static_library_name(self):
        return <string>self.__this__.static_library_name
    @static_library_name.setter
    def static_library_name(self, object value not None):
        self.__this__.static_library_name = <string>u8bytes(value)
    
    @property
    def schedule_name(self):
        return <string>self.__this__.schedule_name
    @schedule_name.setter
    def schedule_name(self, object value not None):
        self.__this__.schedule_name = <string>u8bytes(value)
    
    def object(self, object s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.object(u8bytes(s))
        return out
    
    def assembly(self, object s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.assembly(u8bytes(s))
        return out
    
    def bitcode(self, object s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.bitcode(u8bytes(s))
        return out
    
    def llvm_assembly(self, object s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.llvm_assembly(u8bytes(s))
        return out
    
    def c_header(self, object s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.c_header(u8bytes(s))
        return out
    
    def c_source(self, object s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.c_source(u8bytes(s))
        return out
    
    def python_extension(self, object s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.python_extension(u8bytes(s))
        return out
    
    def stmt(self, object s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.stmt(u8bytes(s))
        return out
    
    def stmt_html(self, object s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.stmt_html(u8bytes(s))
        return out
    
    def static_library(self, object s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.static_library(u8bytes(s))
        return out
    
    def schedule(self, object s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.schedule(u8bytes(s))
        return out
    
    def to_string(self):
        return stringify(self, ("object_name", "assembly_name", "bitcode_name",
                                "llvm_assembly_name", "c_header_name", "c_source_name",
                                "python_extension_name", "stmt_name", "stmt_html_name",
                                "static_library_name", "schedule_name"))
    
    def __bytes__(self):
        return self.to_string()
    
    def __str__(self):
        return self.to_string().decode('UTF-8')
    
    def __repr__(self):
        return self.to_string().decode('UTF-8')


ctypedef GeneratorBase.EmitOptions EmOpts

@cython.freelist(32)
cdef class EmitOptions:
    """ Cython wrapper class for Halide::Internal::GeneratorBase::EmitOptions """
    
    cdef:
        EmOpts __this__
    
    emit_defaults = {
        'emit_o'                : True,
        'emit_h'                : True,
        'emit_cpp'              : False,
        'emit_assembly'         : False,
        'emit_bitcode'          : False,
        'emit_stmt'             : False,
        'emit_stmt_html'        : False,
        'emit_python_extension' : False,
        'emit_static_library'   : True,
        'emit_cpp_stub'         : False,
        'emit_schedule'         : False,
        'substitutions'         : {}
    }
    
    def __cinit__(self, *args, **kwargs):
        for arg in args:
            if type(arg) is type(self):
                self.__this__ = EmOpts()
                self.__this__.emit_o = PyObject_IsTrue(arg.emit_o)
                self.__this__.emit_h = PyObject_IsTrue(arg.emit_h)
                self.__this__.emit_cpp = PyObject_IsTrue(arg.emit_cpp)
                self.__this__.emit_assembly = PyObject_IsTrue(arg.emit_assembly)
                self.__this__.emit_bitcode = PyObject_IsTrue(arg.emit_bitcode)
                self.__this__.emit_stmt = PyObject_IsTrue(arg.emit_stmt)
                self.__this__.emit_stmt_html = PyObject_IsTrue(arg.emit_stmt_html)
                self.__this__.emit_python_extension = PyObject_IsTrue(arg.emit_python_extension)
                self.__this__.emit_static_library = PyObject_IsTrue(arg.emit_static_library)
                self.__this__.emit_cpp_stub = PyObject_IsTrue(arg.emit_cpp_stub)
                self.__this__.emit_schedule = PyObject_IsTrue(arg.emit_schedule)
                for k, v in arg.substitutions.items():
                    self.__this__.substitutions[<string>u8bytes(k)] = <string>u8bytes(v)
                return
        
        emit_o = bool(kwargs.pop('emit_o',                                  self.emit_defaults['emit_o']))
        emit_h = bool(kwargs.pop('emit_h',                                  self.emit_defaults['emit_h']))
        emit_cpp = bool(kwargs.pop('emit_cpp',                              self.emit_defaults['emit_cpp']))
        emit_assembly = bool(kwargs.pop('emit_assembly',                    self.emit_defaults['emit_assembly']))
        emit_bitcode = bool(kwargs.pop('emit_bitcode',                      self.emit_defaults['emit_bitcode']))
        emit_stmt = bool(kwargs.pop('emit_stmt',                            self.emit_defaults['emit_stmt']))
        emit_stmt_html = bool(kwargs.pop('emit_stmt_html',                  self.emit_defaults['emit_stmt_html']))
        emit_python_extension = bool(kwargs.pop('emit_python_extension',    self.emit_defaults['emit_python_extension']))
        emit_static_library = bool(kwargs.pop('emit_static_library',        self.emit_defaults['emit_static_library']))
        emit_cpp_stub = bool(kwargs.pop('emit_cpp_stub',                    self.emit_defaults['emit_cpp_stub']))
        emit_schedule = bool(kwargs.pop('emit_schedule',                    self.emit_defaults['emit_schedule']))
        substitutions = kwargs.pop('substitutions',                         self.emit_defaults['substitutions'])
        
        if not PyMapping_Check(substitutions):
            raise ValueError("substitutions must be a mapping type")
        
        self.__this__.emit_o = PyObject_IsTrue(emit_o)
        self.__this__.emit_h = PyObject_IsTrue(emit_h)
        self.__this__.emit_cpp = PyObject_IsTrue(emit_cpp)
        self.__this__.emit_assembly = PyObject_IsTrue(emit_assembly)
        self.__this__.emit_bitcode = PyObject_IsTrue(emit_bitcode)
        self.__this__.emit_stmt = PyObject_IsTrue(emit_stmt)
        self.__this__.emit_stmt_html = PyObject_IsTrue(emit_stmt_html)
        self.__this__.emit_python_extension = PyObject_IsTrue(emit_python_extension)
        self.__this__.emit_static_library = PyObject_IsTrue(emit_static_library)
        self.__this__.emit_cpp_stub = PyObject_IsTrue(emit_cpp_stub)
        self.__this__.emit_schedule = PyObject_IsTrue(emit_schedule)
        
        for k, v in substitutions.items():
            self.__this__.substitutions[<string>u8bytes(k)] = <string>u8bytes(v)
    
    @property
    def emit_o(self):
        return PyBool_FromLong(self.__this__.emit_o)
    @emit_o.setter
    def emit_o(self, value not None):
        self.__this__.emit_o = PyObject_IsTrue(value)
    
    @property
    def emit_h(self):
        return PyBool_FromLong(self.__this__.emit_h)
    @emit_h.setter
    def emit_h(self, value not None):
        self.__this__.emit_h = PyObject_IsTrue(value)
    
    @property
    def emit_cpp(self):
        return PyBool_FromLong(self.__this__.emit_cpp)
    @emit_cpp.setter
    def emit_cpp(self, value not None):
        self.__this__.emit_cpp = PyObject_IsTrue(value)
    
    @property
    def emit_assembly(self):
        return PyBool_FromLong(self.__this__.emit_assembly)
    @emit_assembly.setter
    def emit_assembly(self, value not None):
        self.__this__.emit_assembly = PyObject_IsTrue(value)
    
    @property
    def emit_bitcode(self):
        return PyBool_FromLong(self.__this__.emit_bitcode)
    @emit_bitcode.setter
    def emit_bitcode(self, value not None):
        self.__this__.emit_bitcode = PyObject_IsTrue(value)
    
    @property
    def emit_stmt(self):
        return PyBool_FromLong(self.__this__.emit_stmt)
    @emit_stmt.setter
    def emit_stmt(self, value not None):
        self.__this__.emit_stmt = PyObject_IsTrue(value)
    
    @property
    def emit_stmt_html(self):
        return PyBool_FromLong(self.__this__.emit_stmt_html)
    @emit_stmt_html.setter
    def emit_stmt_html(self, value not None):
        self.__this__.emit_stmt_html = PyObject_IsTrue(value)
    
    @property
    def emit_python_extension(self):
        return PyBool_FromLong(self.__this__.emit_python_extension)
    @emit_python_extension.setter
    def emit_python_extension(self, value not None):
        self.__this__.emit_python_extension = PyObject_IsTrue(value)
    
    @property
    def emit_static_library(self):
        return PyBool_FromLong(self.__this__.emit_static_library)
    @emit_static_library.setter
    def emit_static_library(self, value not None):
        self.__this__.emit_static_library = PyObject_IsTrue(value)
    
    @property
    def emit_cpp_stub(self):
        return PyBool_FromLong(self.__this__.emit_cpp_stub)
    @emit_cpp_stub.setter
    def emit_cpp_stub(self, value not None):
        self.__this__.emit_cpp_stub = PyObject_IsTrue(value)
    
    @property
    def emit_schedule(self):
        return PyBool_FromLong(self.__this__.emit_schedule)
    @emit_schedule.setter
    def emit_schedule(self, value not None):
        self.__this__.emit_schedule = PyObject_IsTrue(value)
    
    @property
    def substitutions(self):
        return dict(self.__this__.substitutions)
    @substitutions.setter
    def substitutions(self, object value not None):
        if not PyMapping_Check(value):
            raise ValueError("substitutions must be a mapping type")
        self.__this__.substitutions = stringmap_t()
        for k, v in dict(value).items():
            self.__this__.substitutions[<string>u8bytes(k)] = <string>u8bytes(v)
    
    def get_substitution(self, object default):
        return u8bytes(dict(self.__this__.substitutions).get(u8bytes(default),
                                                             u8bytes(default)))
    
    def compute_outputs_for_target_and_path(self,
                                            Target target=Target(),
                                            object base_path=""):
        """ A reimplementation of `compute_outputs()`, private to Halide’s Generator.cpp """
        
        # This is a reimplementation of the C++ orig --
        # ... there used to be some checking here for PNaCl, but all the PNaCl-specific values
        # seem to have vanished from the Halide::Target enums of late. I don’t give much of
        # a whole fuck about PNaCl, personally, so if you are a shit-gifter and you find this
        # behavior to be wrong, please do explain how this wrongness works to me (preferably
        # with a scathingly witty tweet that embarasses me in front of all my friends, and
        # also the greater C++, Cython, and Halide communities in general).
        
        cdef string base_path_str = <string>u8bytes(base_path)
        is_windows_coff = bool(<size_t>target.os == <size_t>OS_Windows and not target.has_feature(<size_t>Feature_MinGW))
        output_files = Outputs()
        
        if self.emit_o:
            if is_windows_coff:
                output_files.object_name = base_path_str + self.get_substitution(".obj")
            else:
                output_files.object_name = base_path_str + self.get_substitution(".o")
        
        if self.emit_assembly:
            output_files.assembly_name = base_path_str + self.get_substitution(".s")
        
        if self.emit_bitcode:
            output_files.bitcode_name = base_path_str + self.get_substitution(".bc")
        if self.emit_h:
            output_files.c_header_name = base_path_str + self.get_substitution(".h")
        if self.emit_cpp:
            output_files.c_source_name = base_path_str + self.get_substitution(".cpp")
        if self.emit_python_extension:
            output_files.stmt_html_name = base_path_str + self.get_substitution(".py.c")
        
        # N.B. Currently the Halide `compute_outputs()` version has no substitution logic
        # for `emit_cpp_stub` -- q.v. Halide/src/Generator.cpp lines 54-96 sub.
        
        if self.emit_stmt:
            output_files.stmt_name = base_path_str + self.get_substitution(".stmt")
        if self.emit_stmt_html:
            output_files.stmt_html_name = base_path_str + self.get_substitution(".html")
        
        if self.emit_static_library:
            if is_windows_coff:
                output_files.static_library_name = base_path_str + self.get_substitution(".lib")
            else:
                output_files.static_library_name = base_path_str + self.get_substitution(".a")
        
        if self.emit_schedule:
            output_files.schedule_name = base_path_str + self.get_substitution(".schedule")
        
        return output_files
    
    def to_string(self):
        return stringify(self, self.emit_defaults.keys())
    
    def __bytes__(self):
        return self.to_string()
    
    def __str__(self):
        return self.to_string().decode('UTF-8')
    
    def __repr__(self):
        return self.to_string().decode('UTF-8')


ctypedef unique_ptr[HalModule] module_ptr_t

cdef class Module:
    """ Cython wrapper class for Halide::Module --
        internally uses a std::unique_ptr<Halide::Module> """
    
    cdef:
        module_ptr_t __this__
    
    def __cinit__(self, *args, **kwargs):
        cdef HalTarget htarg
        for arg in args:
            if type(arg) is type(self):
                htarg = HalTarget(<string>arg.get_target().to_string())
                self.__this__.reset(new HalModule(<string>arg.name, <HalTarget>htarg))
                if self.__this__.get():
                    return
    
    def __init__(self, *args, **kwargs):
        cdef HalTarget htarg
        cdef string name
        cdef string tstring
        if len(args) < 1 and not self.__this__.get():
            name = <string>u8bytes(kwargs.get('name', ''))
            tstring = Target(target_string=kwargs.get('target', 'host')).to_string()
            htarg = HalTarget(tstring)
            self.__this__.reset(new HalModule(name, <HalTarget>htarg))
    
    def __dealloc__(self):
        # Manually calling `reset()` on the internal std::unique_ptr here
        # is not necessary, strictly speaking, as it will reset itself upon
        # scoped stack-deallocation (but who the fuck really knows, rite? huh.)
        self.__this__.reset(NULL)
    
    @property
    def name(self):
        return deref(self.__this__).name()
    
    @property
    def auto_schedule(self):
        return deref(self.__this__).auto_schedule()
    
    @property
    def any_strict_float(self):
        return bool(deref(self.__this__).any_strict_float())
    
    def get_target(self):
        out = Target()
        out.__this__ = deref(self.__this__).target()
        return out
    
    @property
    def target(self):
        return self.get_target()
    
    @staticmethod
    cdef Module with_instance(const HalModule& m):
        cdef Module out = Module()
        with nogil:
            out.__this__.reset(new HalModule(m))
        return out
    
    cdef buffervec_t get_buffers(Module self) nogil:
        cdef buffervec_t out = deref(self.__this__).buffers()
        return out
    
    cdef funcvec_t get_functions(Module self) nogil:
        cdef funcvec_t out = deref(self.__this__).functions()
        return out
    
    cdef modulevec_t get_submodules(Module self) nogil:
        cdef modulevec_t out = deref(self.__this__).submodules()
        return out
    
    def submodules(self):
        cdef modulevec_t modulevec = deref(self.__this__).submodules()
        out = []
        it = modulevec.begin()
        while it != modulevec.end():
            out.append(Module.with_instance(deref(it)))
            incr(it)
        return tuple(out)
    
    def append(self, other not None):
        # Eventually this’ll cover the other Halide::Module::append(…) overloads:
        # Halide::Buffer<void>, Halide::LoweredFunc, and Halide::ExternalCode --
        # which those (at time of writing) do not yet have wrapper cdef-class types:
        cdef Module mother
        if type(other) is type(self):
            mother = <Module>other
            deref(self.__this__).append(deref(mother.__this__))
    
    cdef void replace_instance(Module self, HalModule&& m) nogil:
        self.__this__.reset(new HalModule(m))
    
    def compile(self, Outputs outputs not None):
        cdef HalModule* this = self.__this__.get()
        cdef HalOutputs outs = <HalOutputs>outputs.__this__
        with nogil:
            this.compile(outs)
        return self
    
    def resolve_submodules(self):
        return Module.with_instance(
            deref(self.__this__).resolve_submodules())
    
    def get_metadata(self):
        cdef stringmap_t metadata_map = deref(self.__this__).get_metadata_name_map()
        return dict(metadata_map)
    
    def remap_metadatum_by_name(self, object name, object to_name):
        cdef string name_string = <string>u8bytes(name)
        cdef string to_name_string = <string>u8bytes(to_name)
        deref(self.__this__).remap_metadata_name(name_string,
                                              to_name_string)
        cdef stringmap_t metadata_map = deref(self.__this__).get_metadata_name_map()
        return dict(metadata_map)
    
    def to_string(self):
        cdef string name = <string>deref(self.__this__).name()
        cdef string targ = <string>deref(self.__this__).target().to_string()
        cdef string auto_schedule = <string>deref(self.__this__).auto_schedule()
        cdef stringmap_t metadata_map = deref(self.__this__).get_metadata_name_map()
        cdef string any_strict_float
        any_strict_float_boolean = bool(deref(self.__this__).any_strict_float())
        field_values = (b""" name="%s" """               % name,
                        b""" target="%s" """             % targ)
        if any_strict_float_boolean: # only print if true:
            any_strict_float = any_strict_float_boolean and b"True" or b"False"
            field_values += (b""" any_strict_float=%s """   % any_strict_float,)
        if auto_schedule.size() > 0: # only print if there’s something:
            field_values += (b""" auto_schedule="%s" """ % auto_schedule,)
        if metadata_map.size() > 0: # only print if there’s something:
            metadata_dict = dict(metadata_map)
            # metadata_str = b", ".join(b"%s : “%s”" % (k, v) \
            #                                       for k, v in metadata_dict.items())
            # ... right now the keys and values look to be exactly the same always, sooo:
            metadata_str = b", ".join(b"%s" % k for k in metadata_dict.keys())
            field_values += (b""" metadata={ %s } """ % metadata_str,)
        return b"%s(%s) @ %s" % (u8bytes(type(self).__name__),
                                 b", ".join(field_value.strip() for field_value in field_values),
                                 u8bytes(hex(id(self))))
    
    def __bytes__(self):
        return self.to_string()
    
    def __str__(self):
        return self.to_string().decode('UTF-8')
    
    def __repr__(self):
        return self.to_string().decode('UTF-8')


## FUNCTION WRAPPERS:

def get_host_target():
    """ Halide::get_host_target() wrapper call. """
    return Target.host_target()

def get_target_from_environment():
    """ Halide::get_target_from_environment() wrapper call. """
    return Target.target_from_environment()

def get_jit_target_from_environment():
    """ Halide::get_jit_target_from_environment() wrapper call. """
    return Target.jit_target_from_environment()

cpdef bint validate_target_string(object target_string):
    """ Halide::Target::validate_target_string(s) static method wrapper call. """
    return HalTarget.validate_target_string(<string>u8bytes(target_string))

cpdef set registered_generators():
    """ Enumerate registered generators using Halide::GeneratorRegistry. """
    cdef set out = set()
    cdef tuple names = tuple(GeneratorRegistry.enumerate())
    for enumerated_name in names:
        out |= { u8str(enumerated_name) }
    return out

cdef string halide_compute_base_path(string& output_dir,
                                     string& function_name,
                                     string& file_base_name) nogil:
    cdef stringvec_t namespaces
    cdef string simple_name = halide_extract_namespaces(function_name, namespaces)
    cdef string base_path
    if output_dir.back() == '/':
        base_path = output_dir
    else:
        base_path = output_dir.append('/')
    if file_base_name.empty():
        base_path.append(simple_name)
    else:
        base_path.append(file_base_name)
    return base_path

def compute_base_path(object output_dir not None,
                      object function_name not None,
                      object file_base_name=None):
    """ Reimplementation of Halide::Internal::compute_base_path(...)
        (a private function found in Halide/src/Generator.cpp). """
    cdef string output_dir_string = <string>u8bytes(output_dir)
    cdef string function_name_string = <string>u8bytes(function_name)
    if file_base_name is None:
        file_base_name = ""
    cdef string file_base_name_string = <string>u8bytes(file_base_name)
    return halide_compute_base_path(output_dir_string,
                                    function_name_string,
                                    file_base_name_string)

cpdef Module get_generator_module(object name, object arguments={}):
    """ Retrieve a Halide::Module, wrapped as halogen.api.Module,
        corresponding to the registered generator instance (by name). """
    # first, check name against registered generators:
    if u8str(name) not in registered_generators():
        raise ValueError("""can't find a registered generator named "%s" """ % u8str(name))
    
    # next, check that `arguments` is a mapping type:
    if not PyMapping_Check(arguments):
        raise ValueError(""""arguments" must be a mapping (dict-ish) type""")
    
    # Stack-allocate std::strings for the generator name and target,
    # a unique pointer (for holding a Halide::Target instance),
    # a unique pointer (for holding a Halide::GeneratorBase instance), and
    # a std::map<std::string, Halide::StringOrLoopLevel> (to pass along arguments to Halide):
    cdef string generator_name
    cdef string generator_target
    cdef GeneratorParamsMap argmap
    cdef base_ptr_t generator_instance
    cdef target_ptr_t generator_target_ptr
    
    # Create a new named halogen.api.Module object to return, per the “name” argument:
    out = Module(name=name)
    
    # Convert the Python string value of “name” to a std::string and assign to “generator_name”,
    # and do the same with the potential value arguments['target'] -- defaulting to the string
    # value of halogen.api.Target.target_from_environment():
    generator_name = <string>u8bytes(name)
    generator_target = <string>u8bytes(arguments.pop('target',
                                               Target.target_from_environment().to_string()))
    
    # Copy arguments from the Python dict to the STL map:
    for k, v in arguments.items():
        argmap[<string>u8bytes(k)] = StringOrLoopLevel(<string>u8bytes(v))
    
    with nogil:
        # Heap-allocate a Target object (from either the environment or
        # as per the argument dict) held in a unique pointer:
        generator_target_ptr.reset(
            new HalTarget(generator_target))
        
        # Actually get an instance of the named generator:
        generator_instance = halide_generator_registry_get(generator_name,
                                                     deref(generator_target_ptr))
        
        # Set the generator instances’ argument param values:
        deref(generator_instance).set_generator_param_values(argmap)
        
        # “Modulize” and return the generator instance (which that is a Halide thing, modulization):
        out.replace_instance(
            <HalModule>deref(generator_instance).build_module(generator_name,
                                                              Linkage_Internal))
    
    # return the newly built module:
    return out

cdef void f_insert_into(Module module, modulevec_t& modulevec) nogil:
    modulevec.push_back(deref(module.__this__))

def link_modules(module_name not None, *modules):
    """ Python wrapper for Halide::link_modules() from src/Module.h """
    cdef modulevec_t modulevec
    cdef string name = <string>u8bytes(module_name)
    cdef Module out = Module(name=module_name)
    
    # check that we got some stuff:
    if len(modules) < 1:
        raise ValueError("""link_modules() called without modules to link""")
    
    # check the type of all positional arguments:
    for module in modules:
        if type(module) is not Module:
            raise TypeError("""All positional args must be halogen.api.Module""")
        f_insert_into(module, modulevec)
    
    with nogil:
        out.replace_instance(
            <HalModule>halide_link_modules(name, modulevec))
    
    return out

def compile_standalone_runtime(Target target=Target.target_from_environment(),
                                  object pth=None,
                             Outputs outputs=None):
    """ Compile a standalone Halide runtime library, as directed, per the specified target. """
    # Where we keep the native Options struct, if need be:
    cdef HalOutputs out
    cdef object realpth
    
    # OPTION 1: WE GOT A PATH STRING:
    if pth is not None:
        # real-ify the path - this will raise if problematic:
        from os.path import realpath
        realpth = realpath(u8str(pth))
        if not realpth.lower().endswith('.o'):
            realpth += ".o"
        
        # make the actual call:
        halide_compile_standalone_runtime_for_path(<string>u8bytes(realpth),
                                                   <HalTarget>target.__this__)
        
        # return the real-ified path:
        return u8bytes(realpth)
    
    # OPTION 2: WE GOT A FULL-BLOWN “OUTPUTS” OBJECT:
    elif outputs is not None:
        # confirm the type of the “outputs” object:
        if not Outputs.check(outputs):
            raise TypeError("type(outputs) must be Outputs, not %s" % type(outputs).__name__)
        
        # make the actual call, returning another native Options object:
        with nogil:
            out = halide_compile_standalone_runtime_with_outputs(<HalOutputs>outputs.__this__,
                                                                 <HalTarget>target.__this__)
        
        # return a new halogen.api.Outputs matching the returned value above:
        return Outputs(
            object_name=out.object_name,
            assembly_name=out.assembly_name,
            bitcode_name=out.bitcode_name,
            llvm_assembly_name=out.llvm_assembly_name,
            c_header_name=out.c_header_name,
            c_source_name=out.c_source_name,
            stmt_name=out.stmt_name,
            stmt_html_name=out.stmt_html_name,
            static_library_name=out.static_library_name)
    
    # OPTION 3: WE GOT NEITHER OF THE ABOVE,
    # WHICH MEANS BASICALLY WE CAN DO FUCK-ALL:
    raise ValueError("Either the 'pth' or 'outputs' args must be non-None")

def make_standalone_runtime(Target target=Target.target_from_environment(),
                            object pth=None,
                                 **emitopts):
    # Where to store the output output:
    cdef Outputs outputs
    cdef HalOutputs out
    cdef object realpth
    
    # Sanity-check the passed-in base-path value:
    if pth is None:
        raise ValueError("Must specify 'pth'")
    
    from os.path import realpath
    realpth = realpath(u8str(pth))
    
    # Compute the outputs using halogen.api.EmitOptions -- the EmitOptions defaults
    # will render object files, headers, and archives (.o, .h, .a) --
    # plus, additional emit options can be specified as keyword arguments --
    # HOWEVER, Halide::compile_standalone_runtime() in Module.cpp recreates
    # the Outputs object with only object files and archives (.o, .a) enabled:
    outputs = EmitOptions(**emitopts).compute_outputs_for_target_and_path(t=target,
                                                                  base_path=u8bytes(realpth))
    
    # make the actual call, returning another native Options object:
    with nogil:
        out = halide_compile_standalone_runtime_with_outputs(<HalOutputs>outputs.__this__,
                                                             <HalTarget>target.__this__)
    
    # return a new halogen.api.Outputs matching the returned value above:
    return Outputs(
        object_name=out.object_name,
        assembly_name=out.assembly_name,
        bitcode_name=out.bitcode_name,
        llvm_assembly_name=out.llvm_assembly_name,
        c_header_name=out.c_header_name,
        c_source_name=out.c_source_name,
        stmt_name=out.stmt_name,
        stmt_html_name=out.stmt_html_name,
        static_library_name=out.static_library_name)

def running_program_name():
    """ Return the name of the running program as a string. """
    return halide_running_program_name().decode('UTF-8')
