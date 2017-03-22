#!/usr/bin/env cython
# distutils: language = c++
cimport cython
from cython.operator cimport dereference as deref
from cython.operator cimport address as addr

from libc.stdint cimport *
from libcpp.string cimport string
from libcpp.memory cimport unique_ptr
from cpython.mapping cimport PyMapping_Check
from cpython.long cimport PyLong_AsLong

from ext cimport haldol
#from ext.haldol.terminal cimport terminal_width

from ext.halide.outputs cimport Outputs as HalOutputs
from ext.halide.module cimport Module as HalModule
from ext.halide.module cimport LinkageType

from ext.halide.generator cimport stringmap_t, base_ptr_t
from ext.halide.generator cimport GeneratorBase, GeneratorRegistry
from ext.halide.generator cimport GeneratorContext, JITGeneratorContext
from ext.halide.generator cimport generator_registry_get, generator_registry_create

from ext.halide.type cimport Type as HalType
from ext.halide.type cimport Int as Type_Int
from ext.halide.type cimport UInt as Type_UInt
from ext.halide.type cimport Float as Type_Float
from ext.halide.type cimport Bool as Type_Bool
from ext.halide.type cimport Handle as Type_Handle

from ext.halide.target cimport OS, Arch, Feature
from ext.halide.target cimport Target as HalTarget
from ext.halide.target cimport get_host_target as halide_get_host_target
from ext.halide.target cimport get_target_from_environment as halide_get_target_from_environment
from ext.halide.target cimport get_jit_target_from_environment as halide_get_jit_target_from_environment
from ext.halide.target cimport target_ptr_t
cimport ext.halide.target as target

from ext.halide.util cimport stringvec_t
from ext.halide.util cimport extract_namespaces
from ext.halide.util cimport running_program_name as halide_running_program_name


@cython.freelist(32)
cdef class Type:
    """ Cython wrapper class for Halide::Type """
    
    cdef:
        HalType __this__
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    @staticmethod
    def fromother(Type other):
        out = Type()
        out.__this__ = HalType(other.__this__)
        return out
    
    def __cinit__(Type self, Type other=None, **kwargs):
        if other is not None:
            self.__this__ = HalType(other.__this__)
    
    def __init__(Type self, *args, **kwargs):
        if len(args) < 1:
            if 'code' in kwargs:
                self.__this__ = self.__this__.with_code(kwargs.get('code'))
            elif 'bits' in kwargs:
                self.__this__ = self.__this__.with_bits(<uint8_t>kwargs.get('bits'))
            elif 'lanes' in kwargs:
                self.__this__ = self.__this__.with_lanes(<uint16_t>kwargs.get('lanes'))
    
    @cython.embedsignature(True)
    def code(Type self):
        return self.__this__.code()
    
    @cython.embedsignature(True)
    def bytes(Type self):
        return self.__this__.bytes()
    
    @cython.embedsignature(True)
    def bits(Type self):
        return self.__this__.bits()
    
    @cython.embedsignature(True)
    def lanes(Type self):
        return self.__this__.lanes()
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def with_code(Type self, code):
        out = Type()
        out.__this__ = self.__this__.with_code(code)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def with_bits(Type self, bits):
        out = Type()
        out.__this__ = self.__this__.with_bits(<uint8_t>bits)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def with_lanes(Type self, lanes):
        out = Type()
        out.__this__ = self.__this__.with_lanes(<uint16_t>lanes)
        return out
    
    @cython.embedsignature(True)
    def is_bool(Type self):
        return self.__this__.is_bool()
    
    @cython.embedsignature(True)
    def is_vector(Type self):
        return self.__this__.is_vector()
    
    @cython.embedsignature(True)
    def is_scalar(Type self):
        return self.__this__.is_scalar()
    
    @cython.embedsignature(True)
    def is_float(Type self):
        return self.__this__.is_float()
    
    @cython.embedsignature(True)
    def is_int(Type self):
        return self.__this__.is_int()
    
    @cython.embedsignature(True)
    def is_uint(Type self):
        return self.__this__.is_uint()
    
    @cython.embedsignature(True)
    def is_handle(Type self):
        return self.__this__.is_handle()
    
    @cython.embedsignature(True)
    def same_handle_type(Type self, Type other):
        return self.__this__.same_handle_type(other.__this__)
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def element_of(Type self):
        out = Type()
        out.__this__ = self.__this__.element_of()
        return out
    
    @cython.embedsignature(True)
    def can_represent(Type self, other):
        if type(other) == type(self):
            return self.can_represent_type(other)
        elif type(other) == type(float()):
            return self.can_represent_float(float(other))
        elif type(other) == type(int()) or \
             type(other) == type(long()):
            return self.can_represent_long(long(other))
        return False
    
    def can_represent_type(Type self, Type other):
        return self.__this__.can_represent(other.__this__)
    
    def can_represent_float(Type self, float other):
        return self.__this__.can_represent(<double>other)
    
    def can_represent_long(Type self, long other):
        return self.__this__.can_represent(<int64_t>other)
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    @staticmethod
    def Int(int bits, int lanes=1):
        out = Type()
        out.__this__ = Type_Int(bits, lanes)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    @staticmethod
    def UInt(int bits, int lanes=1):
        out = Type()
        out.__this__ = Type_UInt(bits, lanes)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    @staticmethod
    def Float(int bits, int lanes=1):
        out = Type()
        out.__this__ = Type_Float(bits, lanes)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    @staticmethod
    def Bool(int lanes=1):
        out = Type()
        out.__this__ = Type_Bool(lanes)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    @staticmethod
    def Handle(int lanes=1):
        out = Type()
        out.__this__ = Type_Handle(lanes, NULL)
        return out


@cython.freelist(32)
cdef class Target:
    """ Cython wrapper class for Halide::Target """
    
    cdef:
        HalTarget __this__
    
    @cython.embedsignature(True)
    @staticmethod
    def validate_target_string(string target_string):
        return HalTarget.validate_target_string(target_string)
    
    def __init__(Target self, *args, **kwargs):
        target_string = ''
        if 'target_string' in kwargs:
            target_string = kwargs.get('target_string')
        elif len(args) > 0:
            target_string = args[0]
        if target_string:
            if not HalTarget.validate_target_string(target_string):
                raise ValueError("invalid target string: %s" % target_string)
            self.__this__ = HalTarget(target_string)
    
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
            return self.__this__.bits
        
        def __set__(Target self, value):
            self.__this__.bits = haldol.convert(value)
    
    @cython.embedsignature(True)
    def has_gpu_feature(Target self):
        return self.__this__.has_gpu_feature()
    
    @cython.embedsignature(True)
    def includes_halide_runtime(Target self):
        try:
            return str(self).index('no_runtime') < 0
        except ValueError:
            return True
    
    @cython.embedsignature(True)
    def to_string(Target self):
        return self.__this__.to_string()
    
    @cython.embedsignature(True)
    def maximum_buffer_size(Target self):
        return self.__this__.maximum_buffer_size()
    
    @cython.embedsignature(True)
    def supported(Target self):
        return self.__this__.supported()
    
    @cython.embedsignature(True)
    def supports_type(Target self, Type t):
        return self.__this__.supports_type(t.__this__)
    
    @cython.embedsignature(True)
    def natural_vector_size(Target self, Type t):
        return self.__this__.natural_vector_size(t.__this__)
    
    @cython.embedsignature(True)
    def __str__(Target self):
        return self.__this__.to_string()
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    @staticmethod
    def host_target(Target self):
        out = Target()
        out.__this__ = halide_get_host_target()
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    @staticmethod
    def target_from_environment(Target self):
        out = Target()
        out.__this__ = halide_get_target_from_environment()
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    @staticmethod
    def jit_target_from_environment(Target self):
        out = Target()
        out.__this__ = halide_get_jit_target_from_environment()
        return out


cdef class Outputs:
    
    """ Cython wrapper class for Halide::Outputs """
    
    cdef:
        HalOutputs __this__
    
    @cython.infer_types(True)
    def __init__(Outputs self, *args, **kwargs):
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
        
        object_name = str(kwargs.pop('object_name', ''))
        assembly_name = str(kwargs.pop('assembly_name', ''))
        bitcode_name = str(kwargs.pop('bitcode_name', ''))
        llvm_assembly_name = str(kwargs.pop('llvm_assembly_name', ''))
        c_header_name = str(kwargs.pop('c_header_name', ''))
        c_source_name = str(kwargs.pop('c_source_name', ''))
        stmt_name = str(kwargs.pop('stmt_name', ''))
        stmt_html_name = str(kwargs.pop('stmt_html_name', ''))
        static_library_name = str(kwargs.pop('static_library_name', ''))
        
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
            return self.__this__.object_name
        def __set__(Outputs self, value):
            self.__this__.object_name = <string>value
    
    property assembly_name:
        def __get__(Outputs self):
            return self.__this__.assembly_name
        def __set__(Outputs self, value):
            self.__this__.assembly_name = <string>value
    
    property bitcode_name:
        def __get__(Outputs self):
            return self.__this__.bitcode_name
        def __set__(Outputs self, value):
            self.__this__.bitcode_name = <string>value
    
    property llvm_assembly_name:
        def __get__(Outputs self):
            return self.__this__.llvm_assembly_name
        def __set__(Outputs self, value):
            self.__this__.llvm_assembly_name = <string>value
    
    property c_header_name:
        def __get__(Outputs self):
            return self.__this__.c_header_name
        def __set__(Outputs self, value):
            self.__this__.c_header_name = <string>value
    
    property c_source_name:
        def __get__(Outputs self):
            return self.__this__.c_source_name
        def __set__(Outputs self, value):
            self.__this__.c_source_name = <string>value
    
    property stmt_name:
        def __get__(Outputs self):
            return self.__this__.stmt_name
        def __set__(Outputs self, value):
            self.__this__.stmt_name = <string>value
    
    property stmt_html_name:
        def __get__(Outputs self):
            return self.__this__.stmt_html_name
        def __set__(Outputs self, value):
            self.__this__.stmt_html_name = <string>value
    
    property static_library_name:
        def __get__(Outputs self):
            return self.__this__.static_library_name
        def __set__(Outputs self, value):
            self.__this__.static_library_name = <string>value
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def object(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.object(<string>s)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def assembly(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.assembly(<string>s)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def bitcode(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.bitcode(<string>s)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def llvm_assembly(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.llvm_assembly(<string>s)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def c_header(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.c_header(<string>s)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def c_source(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.c_source(<string>s)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def stmt(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.stmt(<string>s)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def stmt_html(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.stmt_html(<string>s)
        return out
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def static_library(Outputs self, s=None):
        out = Outputs()
        if s is None:
            s = ''
        out.__this__ = self.__this__.static_library(<string>s)
        return out
    
    @cython.embedsignature(True)
    def to_string(Outputs self):
        fields = ("object_name", "assembly_name", "bitcode_name",
                  "llvm_assembly_name", "c_header_name", "c_source_name",
                  "stmt_name", "stmt_html_name", "static_library_name")
        field_dict = {}
        for field in fields:
            field_value = getattr(self, field, "")
            if field_value:
                field_dict.update({ field : field_value })
        field_dict_items = []
        for k, v in field_dict.items():
            field_dict_items.append('''%s="%s"''' % (k, v))
        return "%s(%s) @ %s" % (self.__class__.__name__,
                                ", ".join(field_dict_items),
                                hex(id(self)))
    
    @cython.embedsignature(True)
    def __str__(Outputs self):
        return self.to_string()


ctypedef GeneratorBase.EmitOptions EmOpts

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
        'emit_static_library'   : True
    }
    
    @cython.infer_types(True)
    def __init__(EmitOptions self, *args, **kwargs):
        for arg in args:
            if type(arg) == type(self):
                self.__this__ = EmOpts()
                self.__this__.emit_o = arg.emit_o
                self.__this__.emit_h = arg.emit_h
                self.__this__.emit_cpp = arg.emit_cpp
                self.__this__.emit_assembly = arg.emit_assembly
                self.__this__.emit_bitcode = arg.emit_bitcode
                self.__this__.emit_stmt = arg.emit_stmt
                self.__this__.emit_stmt_html = arg.emit_stmt_html
                self.__this__.emit_static_library = arg.emit_static_library
                for k, v in arg.substitutions.items():
                    self.__this__.substitutions[k] = v
                return
        
        emit_o = bool(kwargs.pop('emit_o',                  self.emit_defaults['emit_o']))
        emit_h = bool(kwargs.pop('emit_h',                  self.emit_defaults['emit_h']))
        emit_cpp = bool(kwargs.pop('emit_cpp',              self.emit_defaults['emit_cpp']))
        emit_assembly = bool(kwargs.pop('emit_assembly',    self.emit_defaults['emit_assembly']))
        emit_bitcode = bool(kwargs.pop('emit_bitcode',      self.emit_defaults['emit_bitcode']))
        emit_stmt = bool(kwargs.pop('emit_stmt',            self.emit_defaults['emit_stmt']))
        emit_stmt_html = bool(kwargs.pop('emit_stmt_html',  self.emit_defaults['emit_stmt_html']))
        emit_static_library = bool(kwargs.pop('emit_static_library',
                                                            self.emit_defaults['emit_static_library']))
        substitutions = kwargs.pop('substitutions',         {})
        
        if not PyMapping_Check(substitutions):
            raise ValueError("substitutions must be a mapping type")
        
        self.__this__.emit_o = <bint>emit_o
        self.__this__.emit_h = <bint>emit_h
        self.__this__.emit_cpp = <bint>emit_cpp
        self.__this__.emit_assembly = <bint>emit_assembly
        self.__this__.emit_bitcode = <bint>emit_bitcode
        self.__this__.emit_stmt = <bint>emit_stmt
        self.__this__.emit_stmt_html = <bint>emit_stmt_html
        self.__this__.emit_static_library = <bint>emit_static_library
        
        for k, v in substitutions.items():
            self.__this__.substitutions[k] = v
    
    property emit_o:
        def __get__(EmitOptions self):
            return self.__this__.emit_o
        def __set__(EmitOptions self, value):
            self.__this__.emit_o = <bint>value
    
    property emit_h:
        def __get__(EmitOptions self):
            return self.__this__.emit_h
        def __set__(EmitOptions self, value):
            self.__this__.emit_h = <bint>value
    
    property emit_cpp:
        def __get__(EmitOptions self):
            return self.__this__.emit_cpp
        def __set__(EmitOptions self, value):
            self.__this__.emit_cpp = <bint>value
    
    property emit_assembly:
        def __get__(EmitOptions self):
            return self.__this__.emit_assembly
        def __set__(EmitOptions self, value):
            self.__this__.emit_assembly = <bint>value
    
    property emit_bitcode:
        def __get__(EmitOptions self):
            return self.__this__.emit_bitcode
        def __set__(EmitOptions self, value):
            self.__this__.emit_bitcode = <bint>value
    
    property emit_stmt:
        def __get__(EmitOptions self):
            return self.__this__.emit_stmt
        def __set__(EmitOptions self, value):
            self.__this__.emit_stmt = <bint>value
    
    property emit_stmt_html:
        def __get__(EmitOptions self):
            return self.__this__.emit_stmt_html
        def __set__(EmitOptions self, value):
            self.__this__.emit_stmt_html = <bint>value
    
    property emit_static_library:
        def __get__(EmitOptions self):
            return self.__this__.emit_static_library
        def __set__(EmitOptions self, value):
            self.__this__.emit_static_library = <bint>value
    
    property substitutions:
        def __get__(EmitOptions self):
            return dict(self.__this__.substitutions)
        def __set__(EmitOptions self, value):
            if not PyMapping_Check(value):
                raise ValueError("substitutions must be a mapping type")
            self.__this__.substitutions = stringmap_t()
            for k, v in dict(value).items():
                self.__this__.substitutions[k] = v
    
    @cython.embedsignature(True)
    def get_substitution(EmitOptions self, string default):
        return dict(self.__this__.substitutions).get(default, default)
    
    @cython.embedsignature(True)
    def compute_outputs_for_target_and_path(EmitOptions self, Target t, string base_path):
        """ A reimplementation of `compute_outputs()`, private to Halide’s Generator.cpp """
        # This is a reimplementation of the C++ orig --
        # there used to be some checking here for PNaCl, but all the PNaCl-specific values
        # seem to have disappeared from the Halide::Target enums. I don’t give much of a
        # whole fuck about PNaCl, personally, so if you do and this behavior is wrong,
        # you should explain how the wrongness works to me (preferably with a scathingly
        # witty tweet that embarasses me in front of all my friends and the greater C++,
        # Cythoin, and Halide communities in general).
        is_windows_coff = bool(t.os == target.Windows and not t.has_feature(target.MinGW))
        base_path_str = str(base_path)
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
        if self.emit_stmt:
            output_files.stmt_name = base_path_str + self.get_substitution(".stmt")
        if self.emit_stmt_html:
            output_files.stmt_html_name = base_path_str + self.get_substitution(".html")
        
        if self.emit_static_library:
            if is_windows_coff:
                output_files.static_library_name = base_path_str + self.get_substitution(".lib")
            else:
                output_files.static_library_name = base_path_str + self.get_substitution(".a")
        
        return output_files

ctypedef unique_ptr[HalModule] module_ptr_t

cdef class Module:
    
    cdef:
        module_ptr_t __this__
    
    def __cinit__(Module self, *args, **kwargs):
        cdef HalTarget htarg
        for arg in args:
            if type(arg) == type(self):
                htarg = HalTarget(<string>arg.target().to_string())
                self.__this__.reset(new HalModule(arg.name(), <HalTarget>htarg))
                return
        self.__this__.reset(new HalModule("", HalTarget('host')))
    
    def __init__(Module self, *args, **kwargs):
        cdef HalTarget htarg
        if len(args) < 1:
            name = kwargs.get('name', '')
            tstring = Target(kwargs.get('target', 'host')).to_string()
            htarg = HalTarget(<string>tstring)
            self.__this__.reset(new HalModule(<string>name, <HalTarget>htarg))
    
    def __dealloc__(Module self):
        self.__this__.reset(NULL)
    
    @cython.embedsignature(True)
    def name(Module self):
        return str(deref(self.__this__).name())
    
    @cython.embedsignature(True)
    @cython.infer_types(True)
    def target(Module self):
        out = Target()
        out.__this__ = deref(self.__this__).target()
        return out
    
    @staticmethod
    cdef Module with_instance(HalModule& m):
        cdef Module out = Module()
        out.__this__.reset(new HalModule(m))
        return out
    
    cdef void replace_instance(Module self, HalModule&& m):
        self.__this__.reset(new HalModule(m))
    
    @cython.embedsignature(True)
    def compile(Module self, Outputs outputs):
        deref(self.__this__).compile(<HalOutputs>outputs.__this__)
    
    @cython.embedsignature(True)
    def to_string(Module self):
        cdef string name = deref(self.__this__).name()
        cdef string targ = deref(self.__this__).target().to_string()
        field_values = [str(name), str(targ)]
        return "%s(%s) @ %s" % (self.__class__.__name__,
                                ", ".join(field_values),
                                hex(id(self)))
    
    @cython.embedsignature(True)
    def __str__(Module self):
        return self.to_string()


## FUNCTION WRAPPERS:
@cython.embedsignature(True)
def get_host_target():
    """ Halide::get_host_target() wrapper call """
    return Target.host_target()

@cython.embedsignature(True)
def get_target_from_environment():
    """ Halide::get_target_from_environment() wrapper call """
    return Target.target_from_environment()

@cython.embedsignature(True)
def get_jit_target_from_environment():
    """ Halide::get_jit_target_from_environment() wrapper call """
    return Target.jit_target_from_environment()

@cython.embedsignature(True)
def validate_target_string(string target_string):
    """ Halide::Target::validate_target_string(s) static method wrapper call """
    return HalTarget.validate_target_string(target_string)

@cython.embedsignature(True)
def registered_generators():
    """ Enumerate registered generators using Halide::GeneratorRegistry """
    out = tuple()
    names = tuple(GeneratorRegistry.enumerate())
    for enumerated_name in names:
        out += tuple([str(enumerated_name)])
    return out

cpdef string halide_compute_base_path(string& output_dir,
                                      string& function_name,
                                      string& file_base_name):
    cdef stringvec_t namespaces
    cdef string simple_name = extract_namespaces(function_name, namespaces)
    cdef string base_path = output_dir + "/"
    if file_base_name.empty():
        base_path += simple_name
    else:
        base_path += file_base_name
    return base_path

@cython.embedsignature(True)
def compute_base_path(string output_dir,
                      string function_name,
                      string file_base_name):
    """ Reimplementation of Halide::Internal::compute_base_path(...)
        (private function from Halide/src/Generator.cpp) """
    return halide_compute_base_path(output_dir,
                                    function_name,
                                    file_base_name)

@cython.embedsignature(True)
cpdef Module get_generator_module(string& name, dict arguments={}):
    """ Retrieve a Halide::Module, wrapped as hal.api.Module,
        corresponding to the registered generator instance (by name) """
    # first, check name against registered generators:
    if str(name) not in registered_generators():
        raise ValueError("""can't find a registered generator named "%s" """ % str(name))
    
    # stack-allocate a named module (per the `name` argument),
    # a unique pointer (for holding a Halide::GeneratorBase instance), and
    # a std::map<std::string, std::string> (to pass along arguments to Halide):
    cdef stringmap_t argmap
    cdef base_ptr_t generator_instance
    out = Module(name=name)
    generator_instance.reset(NULL)
    
    # Heap-allocate a Target object (from either the environment or
    # as per the argument dict) held in a unique pointer:
    t = arguments.get('target', Target.jit_target_from_environment())
    cdef target_ptr_t generator_target
    generator_target.reset(new HalTarget(t.to_string()))
    
    # Copy arguments from the Python dict to the STL map:
    for k, v in arguments.items():
        argmap[<string>k] = <string>v
    
    # Actually get an instance of the named generator:
    generator_instance = generator_registry_get(name, deref(generator_target), argmap)
    
    # “Modulize” and return the generator instance (which that is a Halide thing, modulization):
    out.replace_instance(<HalModule>deref(generator_instance).build_module(name, <LinkageType>0))
    return out

@cython.embedsignature(True)
def running_program_name():
    """ Return the name of the running program as a string. """
    return str(halide_running_program_name())

@cython.embedsignature(True)
cpdef int terminal_width():
    """ Attempt to return the width of the terminal as an integer. """
    cdef int32_t tw = haldol.terminal_width()
    return haldol.convert(tw)

