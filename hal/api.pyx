# distutils: language = c++

from libc.stdint cimport *
from libcpp.string cimport string
from cpython.mapping cimport PyMapping_Check

from outputs cimport Outputs as HalOutputs

from generator cimport GeneratorBase, GeneratorRegistry
from generator cimport stringmap_t

from type cimport Type as HalType
from type cimport Int as Type_Int
from type cimport UInt as Type_UInt
from type cimport Float as Type_Float
from type cimport Bool as Type_Bool
from type cimport Handle as Type_Handle

from target cimport Target as HalTarget
from target cimport OS, Arch, Feature
from target cimport get_host_target as halide_get_host_target
from target cimport get_target_from_environment as halide_get_target_from_environment
from target cimport get_jit_target_from_environment as halide_get_jit_target_from_environment


def registered_generators():
    return tuple(GeneratorRegistry.enumerate())


cdef class Type:
    """ Cython wrapper class for Halide::Type """
    
    cdef:
        HalType __this__
    
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
    
    def code(Type self):
        return self.__this__.code()
    
    def bytes(Type self):
        return self.__this__.bytes()
    
    def bits(Type self):
        return self.__this__.bits()
    
    def lanes(Type self):
        return self.__this__.lanes()
    
    def with_code(Type self, code):
        out = Type()
        out.__this__ = self.__this__.with_code(code)
        return out
    
    def with_bits(Type self, bits):
        out = Type()
        out.__this__ = self.__this__.with_bits(<uint8_t>bits)
        return out
    
    def with_lanes(Type self, lanes):
        out = Type()
        out.__this__ = self.__this__.with_lanes(<uint16_t>lanes)
        return out
    
    def is_bool(Type self):
        return self.__this__.is_bool()
    
    def is_vector(Type self):
        return self.__this__.is_vector()
    
    def is_scalar(Type self):
        return self.__this__.is_scalar()
    
    def is_float(Type self):
        return self.__this__.is_float()
    
    def is_int(Type self):
        return self.__this__.is_int()
    
    def is_uint(Type self):
        return self.__this__.is_uint()
    
    def is_handle(Type self):
        return self.__this__.is_handle()
    
    def same_handle_type(Type self, Type other):
        return self.__this__.same_handle_type(other.__this__)
    
    def element_of(Type self):
        out = Type()
        out.__this__ = self.__this__.element_of()
        return out
    
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
    
    @staticmethod
    def Int(int bits, int lanes=1):
        out = Type()
        out.__this__ = Type_Int(bits, lanes)
        return out
    
    @staticmethod
    def UInt(int bits, int lanes=1):
        out = Type()
        out.__this__ = Type_UInt(bits, lanes)
        return out
    
    @staticmethod
    def Float(int bits, int lanes=1):
        out = Type()
        out.__this__ = Type_Float(bits, lanes)
        return out
    
    @staticmethod
    def Bool(int lanes=1):
        out = Type()
        out.__this__ = Type_Bool(lanes)
        return out
    
    @staticmethod
    def Handle(int lanes=1):
        out = Type()
        out.__this__ = Type_Handle(lanes, NULL)
        return out


cdef class Target:
    """ Cython wrapper class for Halide::Target """
    
    cdef:
        HalTarget __this__
    
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
            return self.__this__.os
            
        def __set__(Target self, value):
            self.__this__.os = <OS>value
        
    property arch:
        
        def __get__(Target self):
            return self.__this__.arch
        
        def __set__(Target self, value):
            self.__this__.arch = <Arch>value
        
    property bits:
        
        def __get__(Target self):
            return self.__this__.bits
        
        def __set__(Target self, value):
            self.__this__.bits = <int>value
    
    def has_gpu_feature(Target self):
        return self.__this__.has_gpu_feature()
    
    def includes_halide_runtime(Target self):
        try:
            return str(self).index('no_runtime') < 0
        except ValueError:
            return True
    
    def to_string(Target self):
        return self.__this__.to_string()
    
    def maximum_buffer_size(Target self):
        return self.__this__.maximum_buffer_size()
    
    def supported(Target self):
        return self.__this__.supported()
    
    def supports_type(Target self, Type t):
        return self.__this__.supports_type(t.__this__)
    
    def natural_vector_size(Target self, Type t):
        return self.__this__.natural_vector_size(t.__this__)
    
    def __str__(Target self):
        return self.__this__.to_string()


cdef class Outputs:
    
    cdef:
        HalOutputs __this__
    
    def __init__(Outputs self, *args, **kwargs):
        for arg in args:
            if type(arg) == type(self):
                self.__this__ = HalOutputs()
                self.__this__.object_name = arg.object_name
                self.__this__.assembly_name = arg.assembly_name
                self.__this__.bitcode_name = arg.bitcode_name
                self.__this__.llvm_assembly_name = arg.llvm_assembly_name
                self.__this__.c_header_name = arg.c_header_name
                self.__this__.c_source_name = arg.c_source_name
                self.__this__.stmt_name = arg.stmt_name
                self.__this__.stmt_html_name = arg.stmt_html_name
                self.__this__.static_library_name = arg.static_library_name
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
        
        self.__this__.object_name = object_name
        self.__this__.assembly_name = assembly_name
        self.__this__.bitcode_name = bitcode_name
        self.__this__.llvm_assembly_name = llvm_assembly_name
        self.__this__.c_header_name = c_header_name
        self.__this__.c_source_name = c_source_name
        self.__this__.stmt_name = stmt_name
        self.__this__.stmt_html_name = stmt_html_name
        self.__this__.static_library_name = static_library_name
    
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
    
    def object(Outputs self, s):
        out = Outputs()
        out.__this__ = self.__this__.object(<string>s)
        return out
    
    def assembly(Outputs self, s):
        out = Outputs()
        out.__this__ = self.__this__.assembly(<string>s)
        return out
    
    def bitcode(Outputs self, s):
        out = Outputs()
        out.__this__ = self.__this__.bitcode(<string>s)
        return out
    
    def llvm_assembly(Outputs self, s):
        out = Outputs()
        out.__this__ = self.__this__.llvm_assembly(<string>s)
        return out
    
    def c_header(Outputs self, s):
        out = Outputs()
        out.__this__ = self.__this__.c_header(<string>s)
        return out
    
    def c_source(Outputs self, s):
        out = Outputs()
        out.__this__ = self.__this__.c_source(<string>s)
        return out
    
    def stmt(Outputs self, s):
        out = Outputs()
        out.__this__ = self.__this__.stmt(<string>s)
        return out
    
    def stmt_html(Outputs self, s):
        out = Outputs()
        out.__this__ = self.__this__.stmt_html(<string>s)
        return out
    
    def static_library(Outputs self, s):
        out = Outputs()
        out.__this__ = self.__this__.static_library(<string>s)
        return out


ctypedef GeneratorBase.EmitOptions EmOpts

cdef class EmitOptions:
    
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
                for k, v in arg.extensions.items():
                    self.__this__.extensions[k] = v
                return
        
        emit_o = kwargs.pop('emit_o',                   self.emit_defaults['emit_o'])
        emit_h = kwargs.pop('emit_h',                   self.emit_defaults['emit_h'])
        emit_cpp = kwargs.pop('emit_cpp',               self.emit_defaults['emit_cpp'])
        emit_assembly = kwargs.pop('emit_assembly',     self.emit_defaults['emit_assembly'])
        emit_bitcode = kwargs.pop('emit_bitcode',       self.emit_defaults['emit_bitcode'])
        emit_stmt = kwargs.pop('emit_stmt',             self.emit_defaults['emit_stmt'])
        emit_stmt_html = kwargs.pop('emit_stmt_html',   self.emit_defaults['emit_stmt_html'])
        emit_static_library = kwargs.pop('emit_static_library',
                                                        self.emit_defaults['emit_static_library'])
        extensions = kwargs.pop('extensions',           dict())
        
        if not PyMapping_Check(extensions):
            raise ValueError("extensions must be a mapping type")
        
        self.__this__.emit_o = emit_o
        self.__this__.emit_h = emit_h
        self.__this__.emit_cpp = emit_cpp
        self.__this__.emit_assembly = emit_assembly
        self.__this__.emit_bitcode = emit_bitcode
        self.__this__.emit_stmt = emit_stmt
        self.__this__.emit_stmt_html = emit_stmt_html
        self.__this__.emit_static_library = emit_static_library
        
        for k, v in extensions.items():
            self.__this__.extensions[k] = v
    
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
    
    property extensions:
        def __get__(EmitOptions self):
            return dict(self.__this__.extensions)
        def __set__(EmitOptions self, value):
            if not PyMapping_Check(value):
                raise ValueError("extensions must be a mapping type")
            self.__this__.extensions = stringmap_t()
            for k, v in dict(value).items():
                self.__this__.extensions[k] = v
    
    def get_extension(EmitOptions self, string default):
        return dict(self.__this__.extensions).get(default, default)
    
    def compute_outputs_for_target_and_path(EmitOptions self, Target target, string base_path):
        # cdef HalOS windows = HalOS.Windows
        # cdef HalFeature mingw = HalFeature.MinGW
        # cdef HalArch pnacl = HalArch.PNaCl
        windows = mingw = pnacl = 0
        is_windows_coff = bool(target.os == windows and not target.has_feature(mingw))
        
        output_files = Outputs()
        
        if self.emit_o:
            if target.arch == pnacl:
                output_files.object_name = str(base_path) + self.get_extension(".bc")
            elif is_windows_coff:
                output_files.object_name = str(base_path) + self.get_extension(".obj")
            else:
                output_files.object_name = str(base_path) + self.get_extension(".o")
        
        if self.emit_assembly:
            output_files.assembly_name = str(base_path) + self.get_extension(".s")
        
        if self.emit_bitcode:
            output_files.bitcode_name = str(base_path) + self.get_extension(".bc")
        if self.emit_h:
            output_files.c_header_name = str(base_path) + self.get_extension(".h")
        if self.emit_cpp:
            output_files.c_source_name = str(base_path) + self.get_extension(".cpp")
        if self.emit_stmt:
            output_files.stmt_name = str(base_path) + self.get_extension(".stmt")
        if self.emit_stmt_html:
            output_files.stmt_html_name = str(base_path) + self.get_extension(".html")
        
        if self.emit_static_library:
            if is_windows_coff:
                output_files.static_library_name = str(base_path) + self.get_extension(".lib")
            else:
                output_files.static_library_name = str(base_path) + self.get_extension(".a")
        
        return output_files


## FUNCTION WRAPPERS:
def get_host_target():
    out = Target()
    out.__this__ = halide_get_host_target()
    return out

def get_target_from_environment():
    out = Target()
    out.__this__ = halide_get_target_from_environment()
    return out

def get_jit_target_from_environment():
    out = Target()
    out.__this__ = halide_get_jit_target_from_environment()
    return out

def validate_target_string(string target_string):
    return HalTarget.validate_target_string(target_string)

