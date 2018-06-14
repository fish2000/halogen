#!/usr/bin/env cython
# distutils: language = c++

import cython
cimport cython
from cython.operator cimport dereference as deref

from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.memory cimport unique_ptr

from cpython.bool cimport PyBool_FromLong
from cpython.long cimport PyLong_AsLong
from cpython.mapping cimport PyMapping_Check
from cpython.object cimport PyObject_IsTrue

from ext.haldol.convert cimport convert as haldol_convert

from ext.halide.outputs cimport Outputs as HalOutputs
from ext.halide.module cimport Module as HalModule
from ext.halide.module cimport LinkageType, LoweredFunc
from ext.halide.module cimport Internal as Linkage_Internal
from ext.halide.module cimport External as Linkage_External
from ext.halide.module cimport funcvec_t
from ext.halide.module cimport modulevec_t
from ext.halide.module cimport link_modules as halide_link_modules
from ext.halide.module cimport halide_compile_standalone_runtime_for_path
from ext.halide.module cimport halide_compile_standalone_runtime_with_outputs

from ext.halide.generator cimport GeneratorBase
from ext.halide.generator cimport GeneratorRegistry
from ext.halide.generator cimport GeneratorContext
from ext.halide.generator cimport stringmap_t
from ext.halide.generator cimport base_ptr_t
from ext.halide.generator cimport generator_registry_get as halide_generator_registry_get
from ext.halide.generator cimport generator_registry_create as halide_generator_registry_create

from ext.halide.type cimport Type as HalType
from ext.halide.type cimport Int as HalType_Int
from ext.halide.type cimport UInt as HalType_UInt
from ext.halide.type cimport Float as HalType_Float
from ext.halide.type cimport Bool as HalType_Bool
from ext.halide.type cimport Handle as HalType_Handle
from ext.halide.type cimport halide_type_to_c_source
from ext.halide.type cimport halide_type_to_c_type
from ext.halide.type cimport halide_type_to_enum_string

from ext.halide.target cimport Target as HalTarget
from ext.halide.target cimport OS, Arch, Feature
from ext.halide.target cimport Windows as OS_Windows
from ext.halide.target cimport MinGW as Feature_MinGW
from ext.halide.target cimport target_ptr_t
from ext.halide.target cimport get_host_target as halide_get_host_target
from ext.halide.target cimport get_target_from_environment as halide_get_target_from_environment
from ext.halide.target cimport get_jit_target_from_environment as halide_get_jit_target_from_environment
cimport ext.halide.target as target

from ext.halide.util cimport stringvec_t
from ext.halide.util cimport extract_namespaces as halide_extract_namespaces
from ext.halide.util cimport running_program_name as halide_running_program_name

from ext.halide.buffer cimport Buffer
from ext.halide.buffer cimport buffervec_t

# from ext.halide.fused cimport stringish_t
# from ext.halide.fused cimport floating_t

@cython.infer_types(True)
def stringify(instance, fields):
    field_dict = {}
    for field in fields:
        field_value = getattr(instance, field, b"")
        if hasattr(field_value, 'decode'):
            field_value = field_value.decode('UTF-8')
        if field_value:
            field_dict.update({ field : field_value })
    field_dict_items = []
    for k, v in field_dict.items():
        field_dict_items.append(b'''%s="%s"''' % (bytes(k,      encoding='UTF-8'),
                                                  bytes(str(v), encoding='UTF-8')))
    return b"%s(%s) @ %s" % (bytes(instance.__class__.__name__,
                                   encoding='UTF-8'),
                            b", ".join(field_dict_items),
                             bytes(hex(id(instance)),
                                   encoding='UTF-8'))


@cython.freelist(32)
cdef class Type:
    """ Cython wrapper class for Halide::Type """
    
    cdef:
        HalType __this__
    
    @cython.infer_types(True)
    @staticmethod
    def fromother(Type other):
        out = Type()
        out.__this__ = HalType(other.__this__)
        return out
    
    def __cinit__(Type self, Type other=None, **kwargs):
        # FIRST: examine `other` argument, looking for an existing Type object,
        # from which we can copy-construct:
        if other is not None:
            if type(other) == type(self):
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
    
    @cython.infer_types(True)
    def code(Type self):
        return self.__this__.code()
    
    @cython.infer_types(True)
    def bytes(Type self):
        return self.__this__.bytes()
    
    @cython.infer_types(True)
    def bits(Type self):
        return self.__this__.bits()
    
    @cython.infer_types(True)
    def lanes(Type self):
        return self.__this__.lanes()
    
    @cython.infer_types(True)
    def with_code(Type self, code):
        out = Type()
        out.__this__ = self.__this__.with_code(code)
        return out
    
    @cython.infer_types(True)
    def with_bits(Type self, bits):
        out = Type()
        out.__this__ = self.__this__.with_bits(<uint8_t>bits)
        return out
    
    @cython.infer_types(True)
    def with_lanes(Type self, lanes):
        out = Type()
        out.__this__ = self.__this__.with_lanes(<uint16_t>lanes)
        return out
    
    @cython.infer_types(True)
    def is_bool(Type self):
        return self.__this__.is_bool()
    
    @cython.infer_types(True)
    def is_vector(Type self):
        return self.__this__.is_vector()
    
    @cython.infer_types(True)
    def is_scalar(Type self):
        return self.__this__.is_scalar()
    
    @cython.infer_types(True)
    def is_float(Type self):
        return self.__this__.is_float()
    
    @cython.infer_types(True)
    def is_int(Type self):
        return self.__this__.is_int()
    
    @cython.infer_types(True)
    def is_uint(Type self):
        return self.__this__.is_uint()
    
    @cython.infer_types(True)
    def is_handle(Type self):
        return self.__this__.is_handle()
    
    @cython.infer_types(True)
    def same_handle_type(Type self, Type other):
        return self.__this__.same_handle_type(other.__this__)
    
    @cython.infer_types(True)
    def element_of(Type self):
        out = Type()
        out.__this__ = self.__this__.element_of()
        return out
    
    @cython.infer_types(True)
    def can_represent(Type self, other):
        if type(other) == type(self):
            return self.can_represent_type(other)
        elif type(other) == type(float()):
            return self.can_represent_float(float(other))
        elif type(other) == type(int()) or \
             type(other) == type(long()):
            return self.can_represent_long(long(other))
        return False
    
    @cython.infer_types(True)
    cpdef object can_represent_type(Type self, Type other):
        return self.__this__.can_represent(other.__this__)
    
    @cython.infer_types(True)
    cpdef object can_represent_float(Type self, float other):
        return self.__this__.can_represent(<double>other)
    
    @cython.infer_types(True)
    cpdef object can_represent_long(Type self, long other):
        return self.__this__.can_represent(<int64_t>other)
    
    @cython.infer_types(True)
    def repr_c_source(Type self):
        try:
            return halide_type_to_c_source(self.__this__)
        except IndexError:
            return "Halide::type_sink<void>"
    
    @cython.infer_types(True)
    def repr_c_type(Type self):
        try:
            return halide_type_to_c_type(self.__this__)
        except IndexError:
            return "void"
    
    @cython.infer_types(True)
    def repr_enum_string(Type self):
        try:
            return halide_type_to_enum_string(self.__this__)
        except IndexError:
            return "void"
    
    @cython.infer_types(True)
    def to_string(Type self):
        try:
            return halide_type_to_c_type(self.__this__)
        except IndexError:
            return "void"
    
    @cython.infer_types(True)
    def __repr__(Type self):
        try:
            c_source = halide_type_to_c_source(self.__this__)
        except IndexError:
            c_source = "Halide::type_sink<void>"
        return str("<%s @ %s>" % (c_source.decode('UTF-8'),
                                  hex(id(self))))
    
    @cython.infer_types(True)
    def __str__(Type self):
        try:
            c_type = halide_type_to_c_type(self.__this__)
        except IndexError:
            c_type = <string>"void"
        return c_type.decode('UTF-8')
    
    @cython.infer_types(True)
    def __bytes__(Type self):
        try:
            c_type = halide_type_to_c_type(self.__this__)
        except IndexError:
            c_type = <string>"void"
        return c_type
    
    @cython.infer_types(True)
    @staticmethod
    def Int(int bits, int lanes=1):
        out = Type()
        out.__this__ = HalType_Int(bits, lanes)
        return out
    
    @cython.infer_types(True)
    @staticmethod
    def UInt(int bits, int lanes=1):
        out = Type()
        out.__this__ = HalType_UInt(bits, lanes)
        return out
    
    @cython.infer_types(True)
    @staticmethod
    def Float(int bits, int lanes=1):
        out = Type()
        out.__this__ = HalType_Float(bits, lanes)
        return out
    
    @cython.infer_types(True)
    @staticmethod
    def Bool(int lanes=1):
        out = Type()
        out.__this__ = HalType_Bool(lanes)
        return out
    
    @cython.infer_types(True)
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
    
    @cython.infer_types(True)
    @staticmethod
    def validate_target_string(string& target_string):
        return HalTarget.validate_target_string(target_string)
    
    def __cinit__(Target self, *args, **kwargs):
        cdef string target_string = b'host'
        if 'target_string' in kwargs:
            target_string = <string>kwargs.get('target_string', b"host")
        elif len(args) > 0:
            target_string = <string>args[0]
        if not HalTarget.validate_target_string(target_string):
            raise ValueError(b"invalid target string: %s" % target_string)
        self.__this__ = HalTarget(target_string)
        # INSERT FEATURE CHECK HERE
    
    property os:
        
        def __get__(Target self):
            return <int>self.__this__.os
            
        def __set__(Target self, value):
            self.__this__.os = <OS>PyLong_AsLong(value)
        
    property arch:
        
        def __get__(Target self):
            return <int>self.__this__.arch
        
        def __set__(Target self, value):
            self.__this__.arch = <Arch>PyLong_AsLong(value)
        
    property bits:
        
        def __get__(Target self):
            return <int>self.__this__.bits
        
        def __set__(Target self, value):
            self.__this__.bits = <int>PyLong_AsLong(value)
    
    @cython.infer_types(True)
    def has_gpu_feature(Target self):
        return self.__this__.has_gpu_feature()
    
    @cython.infer_types(True)
    def has_feature(Target self, feature):
        return self.__this__.has_feature(<Feature>PyLong_AsLong(feature))
    
    @cython.infer_types(True)
    def includes_halide_runtime(Target self):
        try:
            return bytes(self, encoding="UTF-8").index(b'no_runtime') < 0
        except ValueError:
            return True
    
    @cython.infer_types(True)
    def to_string(Target self):
        return self.__this__.to_string()
    
    @cython.infer_types(True)
    def maximum_buffer_size(Target self):
        return self.__this__.maximum_buffer_size()
    
    @cython.infer_types(True)
    def supported(Target self):
        return self.__this__.supported()
    
    @cython.infer_types(True)
    def supports_type(Target self, Type t):
        return self.__this__.supports_type(t.__this__)
    
    @cython.infer_types(True)
    def natural_vector_size(Target self, Type t):
        return self.__this__.natural_vector_size(t.__this__)
    
    @cython.infer_types(True)
    def __str__(Target self):
        return self.__this__.to_string().decode('UTF-8')
    
    @cython.infer_types(True)
    def __bytes__(Target self):
        return self.__this__.to_string()
    
    @cython.infer_types(True)
    def __repr__(Target self):
        return stringify(self, ('os', 'arch', 'bits')).decode('UTF-8')
    
    @cython.infer_types(True)
    def __richcmp__(Target self, Target other, int op):
        if op == 2: # ==
            return bool(<HalTarget>self.__this__ == <HalTarget>other.__this__)
        elif op == 3: # !=
            return bool(<HalTarget>self.__this__ != <HalTarget>other.__this__)
        return False
    
    @cython.infer_types(True)
    @staticmethod
    def host_target():
        out = Target()
        with nogil:
            out.__this__ = halide_get_host_target()
        return out
    
    @cython.infer_types(True)
    @staticmethod
    def target_from_environment():
        out = Target()
        with nogil:
            out.__this__ = halide_get_target_from_environment()
        return out
    
    @cython.infer_types(True)
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
    
    @cython.infer_types(True)
    @classmethod
    def check(cls, instance):
        return getattr(instance, '__class__', None) == cls
    
    def __cinit__(Outputs self, *args, **kwargs):
        for arg in args:
            if type(arg) == type(self):
                self.__this__ = self.__this__.object(arg.object_name) \
                                             .assembly(arg.assembly_name) \
                                             .bitcode(arg.bitcode_name) \
                                             .llvm_assembly(arg.llvm_assembly_name) \
                                             .c_header(arg.c_header_name) \
                                             .c_source(arg.c_source_name) \
                                             .stmt(arg.stmt_name) \
                                             .stmt_html(arg.stmt_html_name) \
                                             .static_library(arg.static_library_name)
                return
        
        object_name = bytes(kwargs.pop('object_name', ''), encoding="UTF-8")
        assembly_name = bytes(kwargs.pop('assembly_name', ''), encoding="UTF-8")
        bitcode_name = bytes(kwargs.pop('bitcode_name', ''), encoding="UTF-8")
        llvm_assembly_name = bytes(kwargs.pop('llvm_assembly_name', ''), encoding="UTF-8")
        c_header_name = bytes(kwargs.pop('c_header_name', ''), encoding="UTF-8")
        c_source_name = bytes(kwargs.pop('c_source_name', ''), encoding="UTF-8")
        stmt_name = bytes(kwargs.pop('stmt_name', ''), encoding="UTF-8")
        stmt_html_name = bytes(kwargs.pop('stmt_html_name', ''), encoding="UTF-8")
        static_library_name = bytes(kwargs.pop('static_library_name', ''), encoding="UTF-8")
        
        self.__this__.object_name = <string>object_name
        self.__this__.assembly_name = <string>assembly_name
        self.__this__.bitcode_name = <string>bitcode_name
        self.__this__.llvm_assembly_name = <string>llvm_assembly_name
        self.__this__.c_header_name = <string>c_header_name
        self.__this__.c_source_name = <string>c_source_name
        self.__this__.stmt_name = <string>stmt_name
        self.__this__.stmt_html_name = <string>stmt_html_name
        self.__this__.static_library_name = <string>static_library_name
    
    property object_name:
        def __get__(Outputs self):
            return bytes(self.__this__.object_name, encoding="UTF-8")
        def __set__(Outputs self, string& value):
            self.__this__.object_name = string(value)
    
    property assembly_name:
        def __get__(Outputs self):
            return str(self.__this__.assembly_name, encoding="UTF-8")
        def __set__(Outputs self, string& value):
            self.__this__.assembly_name = string(value)
    
    property bitcode_name:
        def __get__(Outputs self):
            return bytes(self.__this__.bitcode_name, encoding="UTF-8")
        def __set__(Outputs self, string& value):
            self.__this__.bitcode_name = string(value)
    
    property llvm_assembly_name:
        def __get__(Outputs self):
            return bytes(self.__this__.llvm_assembly_name, encoding="UTF-8")
        def __set__(Outputs self, string& value):
            self.__this__.llvm_assembly_name = string(value)
    
    property c_header_name:
        def __get__(Outputs self):
            return bytes(self.__this__.c_header_name, encoding="UTF-8")
        def __set__(Outputs self, string& value):
            self.__this__.c_header_name = string(value)
    
    property c_source_name:
        def __get__(Outputs self):
            return bytes(self.__this__.c_source_name, encoding="UTF-8")
        def __set__(Outputs self, string& value):
            self.__this__.c_source_name = string(value)
    
    property stmt_name:
        def __get__(Outputs self):
            return bytes(self.__this__.stmt_name, encoding="UTF-8")
        def __set__(Outputs self, string& value):
            self.__this__.stmt_name = string(value)
    
    property stmt_html_name:
        def __get__(Outputs self):
            return bytes(self.__this__.stmt_html_name, encoding="UTF-8")
        def __set__(Outputs self, string& value):
            self.__this__.stmt_html_name = string(value)
    
    property static_library_name:
        def __get__(Outputs self):
            return bytes(self.__this__.static_library_name, encoding="UTF-8")
        def __set__(Outputs self, string& value):
            self.__this__.static_library_name = string(value)
    
    @cython.infer_types(True)
    def object(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.object(<string>s)
        return out
    
    @cython.infer_types(True)
    def assembly(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.assembly(<string>s)
        return out
    
    @cython.infer_types(True)
    def bitcode(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.bitcode(<string>s)
        return out
    
    @cython.infer_types(True)
    def llvm_assembly(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.llvm_assembly(<string>s)
        return out
    
    @cython.infer_types(True)
    def c_header(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.c_header(<string>s)
        return out
    
    @cython.infer_types(True)
    def c_source(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.c_source(<string>s)
        return out
    
    @cython.infer_types(True)
    def stmt(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.stmt(<string>s)
        return out
    
    @cython.infer_types(True)
    def stmt_html(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.stmt_html(<string>s)
        return out
    
    @cython.infer_types(True)
    def static_library(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.static_library(<string>s)
        return out
    
    @cython.infer_types(True)
    def to_string(Outputs self):
        return stringify(self, ("object_name", "assembly_name", "bitcode_name",
                                "llvm_assembly_name", "c_header_name", "c_source_name",
                                "stmt_name", "stmt_html_name", "static_library_name"))
    
    @cython.infer_types(True)
    def __bytes__(Outputs self):
        return self.to_string()
    
    @cython.infer_types(True)
    def __str__(Outputs self):
        return self.to_string().decode('UTF-8')
    
    @cython.infer_types(True)
    def __repr__(Outputs self):
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
        'emit_static_library'   : True,
        'emit_cpp_stub'         : False
    }
    
    def __cinit__(EmitOptions self, *args, **kwargs):
        for arg in args:
            if type(arg) == type(self):
                self.__this__ = EmOpts()
                self.__this__.emit_o = PyObject_IsTrue(arg.emit_o)
                self.__this__.emit_h = PyObject_IsTrue(arg.emit_h)
                self.__this__.emit_cpp = PyObject_IsTrue(arg.emit_cpp)
                self.__this__.emit_assembly = PyObject_IsTrue(arg.emit_assembly)
                self.__this__.emit_bitcode = PyObject_IsTrue(arg.emit_bitcode)
                self.__this__.emit_stmt = PyObject_IsTrue(arg.emit_stmt)
                self.__this__.emit_stmt_html = PyObject_IsTrue(arg.emit_stmt_html)
                self.__this__.emit_static_library = PyObject_IsTrue(arg.emit_static_library)
                self.__this__.emit_cpp_stub = PyObject_IsTrue(arg.emit_cpp_stub)
                for k, v in arg.substitutions.items():
                    self.__this__.substitutions[k] = <string>v
                return
        
        emit_o = bool(kwargs.pop('emit_o',                              self.emit_defaults['emit_o']))
        emit_h = bool(kwargs.pop('emit_h',                              self.emit_defaults['emit_h']))
        emit_cpp = bool(kwargs.pop('emit_cpp',                          self.emit_defaults['emit_cpp']))
        emit_assembly = bool(kwargs.pop('emit_assembly',                self.emit_defaults['emit_assembly']))
        emit_bitcode = bool(kwargs.pop('emit_bitcode',                  self.emit_defaults['emit_bitcode']))
        emit_stmt = bool(kwargs.pop('emit_stmt',                        self.emit_defaults['emit_stmt']))
        emit_stmt_html = bool(kwargs.pop('emit_stmt_html',              self.emit_defaults['emit_stmt_html']))
        emit_static_library = bool(kwargs.pop('emit_static_library',    self.emit_defaults['emit_static_library']))
        emit_cpp_stub = bool(kwargs.pop('emit_cpp_stub',                self.emit_defaults['emit_cpp_stub']))
        substitutions = kwargs.pop('substitutions',                     {})
        
        if not PyMapping_Check(substitutions):
            raise ValueError("substitutions must be a mapping type")
        
        self.__this__.emit_o = PyObject_IsTrue(emit_o)
        self.__this__.emit_h = PyObject_IsTrue(emit_h)
        self.__this__.emit_cpp = PyObject_IsTrue(emit_cpp)
        self.__this__.emit_assembly = PyObject_IsTrue(emit_assembly)
        self.__this__.emit_bitcode = PyObject_IsTrue(emit_bitcode)
        self.__this__.emit_stmt = PyObject_IsTrue(emit_stmt)
        self.__this__.emit_stmt_html = PyObject_IsTrue(emit_stmt_html)
        self.__this__.emit_static_library = PyObject_IsTrue(emit_static_library)
        self.__this__.emit_cpp_stub = PyObject_IsTrue(emit_cpp_stub)
        
        for k, v in substitutions.items():
            self.__this__.substitutions[k] = <string>v
    
    property emit_o:
        def __get__(EmitOptions self):
            return PyBool_FromLong(self.__this__.emit_o)
        def __set__(EmitOptions self, value):
            self.__this__.emit_o = PyObject_IsTrue(value)
    
    property emit_h:
        def __get__(EmitOptions self):
            return PyBool_FromLong(self.__this__.emit_h)
        def __set__(EmitOptions self, value):
            self.__this__.emit_h = PyObject_IsTrue(value)
    
    property emit_cpp:
        def __get__(EmitOptions self):
            return PyBool_FromLong(self.__this__.emit_cpp)
        def __set__(EmitOptions self, value):
            self.__this__.emit_cpp = PyObject_IsTrue(value)
    
    property emit_assembly:
        def __get__(EmitOptions self):
            return PyBool_FromLong(self.__this__.emit_assembly)
        def __set__(EmitOptions self, value):
            self.__this__.emit_assembly = PyObject_IsTrue(value)
    
    property emit_bitcode:
        def __get__(EmitOptions self):
            return self.__this__.emit_bitcode
        def __set__(EmitOptions self, value):
            self.__this__.emit_bitcode = PyObject_IsTrue(value)
    
    property emit_stmt:
        def __get__(EmitOptions self):
            return PyBool_FromLong(self.__this__.emit_stmt)
        def __set__(EmitOptions self, value):
            self.__this__.emit_stmt = PyObject_IsTrue(value)
    
    property emit_stmt_html:
        def __get__(EmitOptions self):
            return PyBool_FromLong(self.__this__.emit_stmt_html)
        def __set__(EmitOptions self, value):
            self.__this__.emit_stmt_html = PyObject_IsTrue(value)
    
    property emit_static_library:
        def __get__(EmitOptions self):
            return PyBool_FromLong(self.__this__.emit_static_library)
        def __set__(EmitOptions self, value):
            self.__this__.emit_static_library = PyObject_IsTrue(value)
    
    property emit_cpp_stub:
        def __get__(EmitOptions self):
            return PyBool_FromLong(self.__this__.emit_cpp_stub)
        def __set__(EmitOptions self, value):
            self.__this__.emit_cpp_stub = PyObject_IsTrue(value)
    
    property substitutions:
        def __get__(EmitOptions self):
            return dict(self.__this__.substitutions)
        def __set__(EmitOptions self, value):
            if not PyMapping_Check(value):
                raise ValueError("substitutions must be a mapping type")
            self.__this__.substitutions = stringmap_t()
            for k, v in dict(value).items():
                self.__this__.substitutions[k] = <string>v
    
    @cython.infer_types(True)
    def get_substitution(EmitOptions self, string& default):
        return dict(self.__this__.substitutions).get(bytes(default, encoding="UTF-8"),
                                                     bytes(default, encoding="UTF-8"))
    
    @cython.infer_types(True)
    def compute_outputs_for_target_and_path(EmitOptions self, Target t, string& base_path):
        """ A reimplementation of `compute_outputs()`, private to Halide’s Generator.cpp """
        # This is a reimplementation of the C++ orig --
        # ... there used to be some checking here for PNaCl, but all the PNaCl-specific values
        # seem to have vanished from the Halide::Target enums of late. I don’t give much of
        # a whole fuck about PNaCl, personally, so if you are a shit-gifter and you find this
        # behavior to be wrong, please do explain how this wrongness works to me (preferably
        # with a scathingly witty tweet that embarasses me in front of all my friends, and
        # also the greater C++, Cython, and Halide communities in general).
        is_windows_coff = bool(<size_t>t.os == <size_t>OS_Windows and not t.has_feature(<size_t>Feature_MinGW))
        base_path_str = bytes(base_path, encoding="UTF-8")
        output_files = Outputs()
        
        if self.emit_o:
            if is_windows_coff:
                output_files.object_name = base_path_str + self.get_substitution(b".obj")
            else:
                output_files.object_name = base_path_str + self.get_substitution(b".o")
        
        if self.emit_assembly:
            output_files.assembly_name = base_path_str + self.get_substitution(b".s")
        
        if self.emit_bitcode:
            output_files.bitcode_name = base_path_str + self.get_substitution(b".bc")
        if self.emit_h:
            output_files.c_header_name = base_path_str + self.get_substitution(b".h")
        if self.emit_cpp:
            output_files.c_source_name = base_path_str + self.get_substitution(b".cpp")
        
        # N.B. Currently the Halide `compute_outputs()` version has no substitution logic
        # for `emit_cpp_stub` -- q.v. Halide/src/Generator.cpp lines 54-96 sub.
        
        if self.emit_stmt:
            output_files.stmt_name = base_path_str + self.get_substitution(b".stmt")
        if self.emit_stmt_html:
            output_files.stmt_html_name = base_path_str + self.get_substitution(b".html")
        
        if self.emit_static_library:
            if is_windows_coff:
                output_files.static_library_name = base_path_str + self.get_substitution(b".lib")
            else:
                output_files.static_library_name = base_path_str + self.get_substitution(b".a")
        
        return output_files
    
    @cython.infer_types(True)
    def to_string(EmitOptions self):
        return stringify(self, list(self.emit_defaults.keys()) + ['substitutions'])
    
    @cython.infer_types(True)
    def __bytes__(EmitOptions self):
        return self.to_string()
    
    @cython.infer_types(True)
    def __str__(EmitOptions self):
        return self.to_string().decode('UTF-8')
    
    @cython.infer_types(True)
    def __repr__(EmitOptions self):
        return self.to_string().decode('UTF-8')


ctypedef unique_ptr[HalModule] module_ptr_t

cdef class Module:
    """ Cython wrapper class for Halide::Module --
        internally uses a std::unique_ptr<Halide::Module> """
    
    cdef:
        module_ptr_t __this__
    
    def __cinit__(Module self, *args, **kwargs):
        cdef HalTarget htarg
        for arg in args:
            if type(arg) == type(self):
                htarg = HalTarget(<string>arg.target().to_string())
                self.__this__.reset(new HalModule(<string>arg.name(), <HalTarget>htarg))
                if self.__this__.get():
                    return
        self.__this__.reset(new HalModule("", HalTarget('host')))
    
    def __init__(Module self, *args, **kwargs):
        cdef HalTarget htarg
        if len(args) < 1 and not self.__this__.get():
            name = bytes(kwargs.get('name', ''), encoding="UTF-8")
            tstring = bytes(Target(bytes(kwargs.get('target', 'host'), encoding="UTF-8")).to_string(), encoding="UTF-8")
            htarg = HalTarget(<string>tstring)
            self.__this__.reset(new HalModule(<string>name, <HalTarget>htarg))
    
    def __dealloc__(Module self):
        # Manually calling `reset()` on the internal std::unique_ptr here
        # is not necessary, strictly speaking, as it will reset itself upon
        # scoped stack-deallocation (but who the fuck really knows, rite? huh.)
        self.__this__.reset(NULL)
    
    @cython.infer_types(True)
    def name(Module self):
        return bytes(deref(self.__this__).name(), encoding="UTF-8")
    
    @cython.infer_types(True)
    def target(Module self):
        out = Target()
        out.__this__ = deref(self.__this__).target()
        return out
    
    @cython.infer_types(True)
    @staticmethod
    cdef Module with_instance(HalModule& m):
        cdef Module out = Module()
        with nogil:
            out.__this__.reset(new HalModule(m))
        return out
    
    @cython.infer_types(True)
    cdef buffervec_t buffers(Module self):
        cdef buffervec_t out = deref(self.__this__).buffers()
        return out
    
    @cython.infer_types(True)
    cdef funcvec_t functions(Module self):
        cdef funcvec_t out = deref(self.__this__).functions()
        return out
    
    @cython.infer_types(True)
    cdef void replace_instance(Module self, HalModule&& m) nogil:
        self.__this__.reset(new HalModule(m))
    
    @cython.infer_types(True)
    def compile(Module self, Outputs outputs):
        deref(self.__this__).compile(<HalOutputs>outputs.__this__)
    
    @cython.infer_types(True)
    def to_string(Module self):
        cdef string name = deref(self.__this__).name()
        cdef string targ = deref(self.__this__).target().to_string()
        field_values = [b"name=%s" % bytes(name, encoding="UTF-8"),
                        b"target=%s" % bytes(targ, encoding="UTF-8")]
        return b"%s(%s) @ %s" % (bytes(self.__class__.__name__,
                                       encoding="UTF-8"),
                                b", ".join(field_values),
                                 bytes(hex(id(self)),
                                       encoding="UTF-8"))
    
    @cython.infer_types(True)
    def __bytes__(Module self):
        return self.to_string()
    
    @cython.infer_types(True)
    def __str__(Module self):
        return self.to_string().decode('UTF-8')
    
    @cython.infer_types(True)
    def __repr__(Module self):
        return self.to_string().decode('UTF-8')


## FUNCTION WRAPPERS:
@cython.infer_types(True)
def get_host_target():
    """ Halide::get_host_target() wrapper call. """
    return Target.host_target()

@cython.infer_types(True)
def get_target_from_environment():
    """ Halide::get_target_from_environment() wrapper call. """
    return Target.target_from_environment()

@cython.infer_types(True)
def get_jit_target_from_environment():
    """ Halide::get_jit_target_from_environment() wrapper call. """
    return Target.jit_target_from_environment()

@cython.infer_types(True)
cpdef bint validate_target_string(string& target_string):
    """ Halide::Target::validate_target_string(s) static method wrapper call. """
    return HalTarget.validate_target_string(<string>target_string)

@cython.infer_types(True)
def registered_generators():
    """ Enumerate registered generators using Halide::GeneratorRegistry. """
    out = tuple()
    names = tuple(GeneratorRegistry.enumerate())
    for enumerated_name in names:
        out += tuple([enumerated_name])
    return out

cdef string halide_compute_base_path(string& output_dir,
                                     string& function_name,
                                     string& file_base_name):
    cdef stringvec_t namespaces
    cdef string simple_name = halide_extract_namespaces(function_name, namespaces)
    cdef string base_path = output_dir + "/"
    if file_base_name.empty():
        base_path += simple_name
    else:
        base_path += file_base_name
    return base_path

@cython.infer_types(True)
def compute_base_path(string& output_dir,
                      string& function_name,
                      string& file_base_name):
    """ Reimplementation of Halide::Internal::compute_base_path(...)
        (a private function found in Halide/src/Generator.cpp). """
    return halide_compute_base_path(output_dir,
                                    function_name,
                                    file_base_name)

@cython.infer_types(True)
cpdef Module get_generator_module(string& name, object arguments={}):
    """ Retrieve a Halide::Module, wrapped as hal.api.Module,
        corresponding to the registered generator instance (by name). """
    # first, check name against registered generators:
    if bytes(name, encoding="UTF-8") not in registered_generators():
        raise ValueError(b"""can't find a registered generator named "%s" """ % bytes(name, encoding="UTF-8"))
    
    # next, check that `arguments` is a mapping type:
    if not PyMapping_Check(arguments):
        raise ValueError(b""""arguments" must be a mapping (dict-ish) type""")
    
    # stack-allocate a named module (per the `name` argument),
    # a unique pointer (for holding a Halide::GeneratorBase instance), and
    # a std::map<std::string, std::string> (to pass along arguments to Halide):
    cdef stringmap_t argmap
    cdef base_ptr_t generator_instance
    out = Module(name=name)
    
    # Heap-allocate a Target object (from either the environment or
    # as per the argument dict) held in a unique pointer:
    t = arguments.get('target', Target.target_from_environment().to_string())
    cdef target_ptr_t generator_target
    generator_target.reset(new HalTarget(<string>t))
    
    # Copy arguments from the Python dict to the STL map:
    for k, v in arguments.items():
        argmap[<string>k] = <string>v
    
    with nogil:
        # Actually get an instance of the named generator:
        generator_instance = halide_generator_registry_get(name, deref(generator_target), argmap)
        
        # “Modulize” and return the generator instance (which that is a Halide thing, modulization):
        out.replace_instance(<HalModule>deref(generator_instance).build_module(name, Linkage_Internal))
    return out

cdef void f_insert_into(Module module, modulevec_t& modulevec) nogil:
    modulevec.push_back(deref(module.__this__))

@cython.infer_types(True)
def link_modules(string& module_name, *modules):
    """ Python wrapper for Halide::link_modules() from src/Module.h """
    cdef modulevec_t modulevec
    out = Module(name=module_name)
    
    # check that we got some stuff:
    if len(modules) < 1:
        raise ValueError(b"""link_modules() called without modules to link""")
    
    # check the type of all positional arguments:
    for module in modules:
        if type(module) is not type(Module):
            raise TypeError(b"""All positional args must be hal.api.Module""")
    
    for module in modules:
        f_insert_into(module, modulevec)
    
    out.replace_instance(<HalModule>halide_link_modules(module_name, modulevec))
    return out

@cython.infer_types(True)
def compile_standalone_runtime(Target target=Target.target_from_environment(),
                                  object pth=None,
                             Outputs outputs=None):
    """ Compile a standalone Halide runtime library, as directed, per the specified target. """
    # Where we keep the native Options struct, if need be:
    cdef HalOutputs out
    
    # OPTION 1: WE GOT A PATH STRING:
    if pth is not None:
        # real-ify the path - this will raise if problematic:
        from os.path import realpath
        realpth = realpath(pth)
        if not realpth.lower().endswith(b'.o'):
            realpth += b".o"
        
        # make the actual call:
        halide_compile_standalone_runtime_for_path(<string>realpth,
                                                   <HalTarget>target.__this__)
        
        # return the real-ified path:
        return bytes(realpth, encoding="UTF-8")
    
    # OPTION 2: WE GOT A FULL-BLOWN “OUTPUTS” OBJECT:
    elif outputs is not None:
        # confirm the type of the “outputs” object:
        if not Outputs.check(outputs):
            raise TypeError("type(outputs) must be Outputs, not %s" % outputs.__class__.__name__)
        
        # make the actual call, returning another native Options object:
        with nogil:
            out = halide_compile_standalone_runtime_with_outputs(<HalOutputs>outputs.__this__,
                                                                 <HalTarget>target.__this__)
        
        # return a new hal.api.Outputs matching the returned value above:
        return Outputs(
            object_name=bytes(out.object_name, encoding="UTF-8"),
            assembly_name=bytes(out.assembly_name, encoding="UTF-8"),
            bitcode_name=bytes(out.bitcode_name, encoding="UTF-8"),
            llvm_assembly_name=bytes(out.llvm_assembly_name, encoding="UTF-8"),
            c_header_name=bytes(out.c_header_name, encoding="UTF-8"),
            c_source_name=bytes(out.c_source_name, encoding="UTF-8"),
            stmt_name=bytes(out.stmt_name, encoding="UTF-8"),
            stmt_html_name=bytes(out.stmt_html_name, encoding="UTF-8"),
            static_library_name=bytes(out.static_library_name, encoding="UTF-8"))
    
    # OPTION 3: WE GOT NEITHER OF THE ABOVE,
    # WHICH MEANS BASICALLY WE CAN DO FUCK-ALL:
    raise ValueError("Either the 'pth' or 'outputs' args must be non-None")

@cython.infer_types(True)
def make_standalone_runtime(Target target=Target.target_from_environment(),
                            object pth=None):
    # Where to store the output output:
    cdef Outputs outputs
    cdef HalOutputs out
    
    # Sanity-check the passed-in base-path value:
    if pth is None:
        raise ValueError("Must specify 'pth'")
    
    from os.path import realpath
    realpth = realpath(pth)
    
    # Compute the outputs using hal.api.EmitOptions -- the EmitOptions defaults
    # will render object files, headers, and archives (.o, .h, .a) --
    # HOWEVER, Halide::compile_standalone_runtime() in Module.cpp recreates
    # the Outputs object with only object files and archives (.o, .a) enabled:
    outputs = EmitOptions().compute_outputs_for_target_and_path(t=target,
                                                        base_path=<string>realpth)
    
    # make the actual call, returning another native Options object:
    with nogil:
        out = halide_compile_standalone_runtime_with_outputs(<HalOutputs>outputs.__this__,
                                                             <HalTarget>target.__this__)
    
    # return a new hal.api.Outputs matching the returned value above:
    return Outputs(
        object_name=bytes(out.object_name, encoding="UTF-8"),
        assembly_name=bytes(out.assembly_name, encoding="UTF-8"),
        bitcode_name=bytes(out.bitcode_name, encoding="UTF-8"),
        llvm_assembly_name=bytes(out.llvm_assembly_name, encoding="UTF-8"),
        c_header_name=bytes(out.c_header_name, encoding="UTF-8"),
        c_source_name=bytes(out.c_source_name, encoding="UTF-8"),
        stmt_name=bytes(out.stmt_name, encoding="UTF-8"),
        stmt_html_name=bytes(out.stmt_html_name, encoding="UTF-8"),
        static_library_name=bytes(out.static_library_name, encoding="UTF-8"))

@cython.infer_types(True)
def running_program_name():
    """ Return the name of the running program as a string. """
    return halide_running_program_name().decode('UTF-8')
