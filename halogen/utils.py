# -*- coding: utf-8 -*-

from __future__ import print_function

# import builtins
import six
import sys
import types
import typing as tx

from functools import wraps

__all__ = ('ty', 'find_generic_for_type',
           'TerminalSize', 'terminal_size',
                           'terminal_width',
                           'terminal_height',
           'tuplize', 'listify',
           'wrap_value', 'Memoizer', 'memoize',
           'current_umask', 'masked_permissions',
           'modulize',
           'append_paths', 'remove_paths',
           'string_types', 'is_string', 'stringify',
                                        'u8bytes',
                                        'u8str',
           'suffix_searcher',
           'terminal_print', 'print_cache',
                             'print_config',
                             'test_compile')

__dir__ = lambda: list(__all__)

ty = types.SimpleNamespace()

# build a “for_origin” dict in the “ty” namespace:
ty.for_origin: tx.Dict[str, type] = {}
for key in tx.__dir__():
    txattr = getattr(tx, key)
    if hasattr(txattr, '__origin__'):
        origin = txattr.__origin__
        ty.for_origin[origin] = txattr
        ty.__setattr__(origin.__name__, txattr)

# build a “for_name” dict in the “ty” namespace:
# ty.for_name: tx.Dict[str, type] = {}
# for tup in builtins.__dict__.items():
#     if type(tup[1]) == type:
#         builtin = tup[1]
#         ty.for_name[]

ConcreteType = tx.TypeVar('ConcreteType', bound=type, covariant=True)

def find_generic_for_type(T: tx.Type[ConcreteType]) -> tx.Optional[type]:
    if not hasattr(T, '__mro__'):
        return None
    for t in T.__mro__:
        if t in ty.for_origin:
            return ty.for_origin.get(t)
    return None


class TerminalSize(object):
    
    class Size(tx.NamedTuple):
        
        height: int = 25
        width: int = 120
        
        @property
        def area(self) -> int:
            """ Compute total area """
            return self.width * self.height
        
        @property
        def perimeter(self) -> int:
            """ Calculate perimeter of the size’s bounding box """
            return (self.width * 2) + \
                   (self.height * 2)
        
        @property
        def lines(self) -> int:
            """ known also as how high, the height, the tallness … """
            return self.height
        
        @property
        def columns(self) -> int:
            """ a.k.a how long, width, the x-dimension etc """
            return self.width
        
        def copy(self) -> tx.NamedTuple:
            """ Duplicate the Size instance """
            return self._replace(
                 **self._asdict())
    
    DEFAULT_LINES:   int = 25
    DEFAULT_COLUMNS: int = 130
    MINIMUM_LINES:   int = 25
    MINIMUM_COLUMNS: int = 25
    
    cache: tx.List[Size] = []
    
    @staticmethod
    def ioctl_GWINSZ(descriptor: int) -> tx.Optional[
                                         tx.Tuple[int, int]]:
        """ Extract the GWINSZ terminal I/O property value data
            from a file descriptor, using an `ioctl(…)` call to
            obtain the packed Posix data structure, a call to the
           `struct.unpack(…)` module to process the raw ioctl output
            into Python integers
        """
        
        import fcntl, termios, struct
        try:
            cr: tx.Tuple[int, int] = struct.unpack('hh',
                                      fcntl.ioctl(descriptor,
                                                  termios.TIOCGWINSZ,
                                                 '1234'))
        except:
            return None
        return cr
    
    def __init__(self, DEFAULT_LINES:   tx.Optional[int] = None,
                       DEFAULT_COLUMNS: tx.Optional[int] = None):
        
        """ Initialize the TerminalSize babysitter class """
        
        if DEFAULT_LINES is not None:
            if self.DEFAULT_LINES   !=   DEFAULT_LINES and \
               self.MINIMUM_LINES   <=   DEFAULT_LINES:
               self.DEFAULT_LINES   =    DEFAULT_LINES
        
        if DEFAULT_COLUMNS is not None:
            if self.DEFAULT_COLUMNS != DEFAULT_COLUMNS and \
               self.MINIMUM_COLUMNS <= DEFAULT_COLUMNS:
               self.DEFAULT_COLUMNS =  DEFAULT_COLUMNS
        
        self.store_terminal_size()
        
    def fetch_terminal_size_values(self) -> tx.Tuple[int, int]:
        import os
        env = os.environ
        
        # Adapted from this: http://stackoverflow.com/a/566752/298171
        # … first, attempt to pluck out the CGWINSZ terminal values using
        # the stdin/stdout/stderr file descriptor numbers:
        cr: tx.Optional[
            tx.Tuple[int, int]] = self.ioctl_GWINSZ(0) or \
                                  self.ioctl_GWINSZ(1) or \
                                  self.ioctl_GWINSZ(2)
        
        # … if that did not work, get the /dev entry name of the terminal
        # in which our process is ensconced, open a descriptor on it for reaing,
        # and use that descriptor to once again attempt to read CGWINSZ values 
        # for the terminal:
        descriptor: int = 0
        if not cr:
            try:
                descriptor = os.open(os.ctermid(),
                                     os.O_RDONLY)
                cr: tx.Optional[
                    tx.Tuple[int, int]] = self.ioctl_GWINSZ(descriptor)
            except:
                pass
            finally:
                if descriptor:
                    os.close(descriptor)
        
        # … if we were unsuccessfull in reading from all three of the standard I/O
        # descriptors •and• a bespoke descriptor opened directly on the /dev entry,
        # make a last-ditch effort to send back values culled from the environment,
        # with truly last-resort possibilities filled in with hardcoded defaults.
        if not cr:
            cr = (env.get('LINES',   self.DEFAULT_LINES),
                  env.get('COLUMNS', self.DEFAULT_COLUMNS))
        
        # Return plain tuple:
        return cr
    
    def store_terminal_size(self) -> Size:
        size: self.Size = self.Size(*self.fetch_terminal_size_values())
        self.cache.append(size)
        return size
    
    def __call__(self, *args, **kwargs) -> Size:
        if len(self.cache) < 1:
            self.store_terminal_size()
        return self.cache[-1]

terminal_size: TerminalSize = TerminalSize()
terminal_width:  int        = terminal_size().width 
terminal_height: int        = terminal_size().height

StringType = tx.TypeVar('StringType', bound=type, covariant=True)

string_types: tx.Tuple[tx.Type[StringType], ...] = (type(''),
                                                    type(b''),
                                                    type(f''),
                                                    type(r'')) + six.string_types

is_string: tx.Callable[[tx.Any], bool] = lambda thing: isinstance(thing, string_types)

def tuplize(*items) -> tuple:
    return tuple(item for item in items if item is not None)

def listify(*items) -> list:
    return list(item for item in items if item is not None)

WrapArg = tx.TypeVar('WrapArg', covariant=True)

def wrap_value(value: tx.Any) -> tx.Callable[[tx.Optional[tx.Iterable[tx.Any]],
                                              tx.Optional[tx.Mapping[tx.Any,
                                                                     tx.Any]]],
                                             tx.Any]:
    return lambda *args, **kwargs: value

class Memoizer(dict):
    
    def __init__(self, function=None):
        super(Memoizer, self).__init__()
        if function is None:
            function = wrap_value(function)
        self.original_function = (function,)
    
    def __missing__(self, key):
        function = self.original_function[0]
        self[key] = out = function(*key)
        return out
    
    @property
    def original(self):
        return self.original_function[0]
    
    @original.setter
    def original(self, value):
        if not callable(value):
            value = wrap_value(value)
        self.original_function = (value,)
    
    def __call__(self, function):
        @wraps(function)
        def memoized(*args):
            return self[args]
        self.original = function
        memoized.original = function
        return memoized

def memoize(function):
    memoinstance = Memoizer(function)
    @wraps(function)
    def memoized(*args):
        return memoinstance[args]
    memoized.original = function
    return memoized

@memoize
def current_umask():
    import os
    mask = os.umask(0)
    os.umask(mask)
    return mask

def masked_permissions(perms=0o666):
    return perms & ~current_umask()

def modulize(namespace: tx.MutableMapping[str, tx.Any],
             modulename: str,
             moduledocs: tx.Optional[str] = None,
             modulefile: tx.Optional[str] = None) -> types.ModuleType:
    
    """ Convert a dictionary mapping into a legit Python module """
    
    import os
    import re
    
    # Update the namespace with '__all__' and '__dir__':
    if '__all__' not in namespace:
        ns_all = tuplize(*sorted(namespace.keys()))
        namespace.update({
            '__all__' : ns_all,
            '__dir__' : lambda: list(ns_all)
        })
    
    # Create a new module with a trivially namespaced name:
    if modulefile:
        relpath: str = os.path.relpath(modulefile,
                 start=os.path.dirname(__file__))
        dotpath = re.sub(re.compile(rf"({os.path.sep})"), os.path.extsep, relpath)
        if dotpath.endswith('.py'):
            dotpath = dotpath[:len(dotpath)-3]
        namespacedname: str = f'__dynamic_modules__.halogen.{dotpath}.{modulename}'
        namespace.update({ '__file__' : modulefile })
    else:
        namespacedname: str = f'__dynamic_modules__.halogen.{modulename}'
    namespace.update({ '__package__' : namespacedname })
    
    module = types.ModuleType(namespacedname, moduledocs)
    module.__dict__.update(namespace)
    
    # Add to sys.modules, as per import machinery:
    sys.modules.update({ modulename : module })
    
    # Return the new module instance:
    return module

def append_paths(*putatives) -> tx.Dict[str, bool]:
    """ Mutate `sys.path` by appending one or more new paths -- all of which
        are checked for both nonexistence and presence within the existing
        `sys.path` list via inode lookup, and which those failing such checks
        are summarily excluded.
    """
    import os
    out: tx.Dict[str, bool] = {}
    if len(putatives) < 1:
        return out
    paths: tx.Set[str] = set(sys.path)
    append_paths.oldsyspath: tx.Tuple[str, ...] = tuple(sys.path)
    for pth in putatives:
        if hasattr(pth, 'name'):
            pth = pth.name
        if not os.path.exists(pth):
            out[pth] = False
            continue
        # if pth in paths:
        #     out[pth] = False
        #     continue
        for p in paths:
            if os.path.samefile(p, pth):
                out[pth] = False
                continue
        sys.path.append(pth)
        out[pth] = True
        continue
    return out

append_paths.oldsyspath: tx.Tuple[str, ...] = tuple()

def remove_paths(*putatives) -> tx.Dict[str, bool]:
    """ Mutate `sys.path` by removing one or more existing paths --
        all of which are checked for presence within the existing `sys.path`
        list via inode lookup before being marked for removal, which that
        (the removal) is done atomically.
    """
    import os
    out: tx.Dict[str, bool] = {}
    if len(putatives) < 1:
        return out
    removals: tx.Set[str] = set()
    paths: tx.Set[str] = set(sys.path)
    for pth in putatives:
        if hasattr(pth, 'name'):
            pth = pth.name
        for p in paths:
            if os.path.samefile(p, pth):
                out[pth] = True
                removals |= { p }
                continue
        out[pth] = False
        continue
    paths -= removals
    remove_paths.oldsyspath: tx.Tuple[str, ...] = tuple(sys.path)
    sys.path = list(paths)
    return out

remove_paths.oldsyspath: tx.Tuple[str, ...] = tuple()

def u8encode(source: tx.Any) -> bytes:
    """ Encode a source as bytes using the UTF-8 codec """
    return bytes(source, encoding='UTF-8')

def u8bytes(source: tx.Any) -> bytes:
    """ Encode a source as bytes using the UTF-8 codec, guaranteeing a
        proper return value without raising an error
    """
    if type(source) == bytes:
        return source
    elif type(source) == str:
        return u8encode(source)
    elif isinstance(source, six.string_types):
        return u8encode(source)
    elif isinstance(source, (int, float)):
        return u8encode(str(source))
    elif type(source) == bool:
        return source and b'True' or b'False'
    elif source is None:
        return b'None'
    return bytes(source)

def u8str(source: tx.Any) -> str:
    """ Encode a source as a Python string, guaranteeing a proper return
        value without raising an error
    """
    return u8bytes(source).decode('UTF-8')

def stringify(instance: tx.Any, fields: tx.Iterable[str]) -> str:
    """ Stringify an object instance, using an iterable field list to
        extract and render its values, and printing them along with the 
        typename of the instance and its memory address -- yielding a
        repr-style string of the format:
        
            TypeName(fieldname="val", otherfieldname="otherval") @ 0x0FE
        
        The `stringify(…)` function is of use in `__str__()` and `__repr__()`
        definitions, E.G. something like:
        
            def __repr__(self):
                return stringify(self, type(self).__slots__)
        
    """
    field_dict: tx.Dict[str, str] = {}
    for field in fields:
        field_value = getattr(instance, field, "")
        field_value = callable(field_value) and field_value() or field_value
        if field_value:
            field_dict.update({ str(field) : field_value })
    field_dict_items: tx.List[str] = []
    for k, v in field_dict.items():
        field_dict_items.append(f'''{k}="{v}"''')
    typename: str = type(instance).__name__
    field_dict_string: str = ", ".join(field_dict_items)
    hex_id: str = hex(id(instance))
    return f"{typename}({field_dict_string}) @ {hex_id}"

def suffix_searcher(suffix: str) -> tx.Callable[[tx.AnyStr], bool]:
    """ Return a boolean function that will search for the given
        file suffix in strings with which it is called, returning
        True when they are found and False when they aren’t.
        
        Useful in filter(…) calls and comprehensions, e.g.:
        
        >>> plists = filter(suffix_searcher('plist'), os.listdir())
        >>> mmsuffix = suffix_searcher('mm')
        >>> objcpp = (f for f in os.listdir() where mmsuffix(f))
    """
    import re, os
    if len(suffix) < 1:
        return lambda searching_for: True
    regex_str: str = r""
    if suffix.startswith(os.extsep):
        regex_str += rf"\{suffix}$"
    else:
        regex_str += rf"\{os.extsep}{suffix}$"
    searcher = re.compile(regex_str, re.IGNORECASE).search
    return lambda searching_for: bool(searcher(searching_for))

def terminal_print(message: str,
                   handle: tx.Any = sys.stdout,
                   color: str = 'red',
                   asterisk: str = '*'):
    """ Print a string to the terminal, centered and bookended with asterisks
    """
    from clint.textui.colored import red
    from clint.textui import colored
    
    colorizer = getattr(colored, color.lower(), red)
    message: str = f" {message.strip()} "
    width: int = terminal_size().width
    
    asterisks: int = (width / 2) - (len(message) / 2)
    aa: str = asterisk[0] * asterisks
    ab: str = asterisk[0] * (asterisks + 0 - (len(message) % 2))
    
    print(colorizer(f"{aa}{message}{ab}"), file=handle)

def print_cache(BaseClass: type, cache_instance_name: str):
    """ Pretty-print the contents of a cached metaclass variable """
    from pprint import pprint
    
    instance: tx.Any = getattr(BaseClass, cache_instance_name)
    qualname: str = f"{BaseClass.__name__}.{cache_instance_name}"
    entrycnt: int = len(instance)
    dicttype: str = type(instance).__name__
    
    width: int = terminal_size().width
    
    print("=" * width)
    print("")
    print(f" • DUMPING METACLASS CACHE « {qualname}: {dicttype} »")
    print(f" • CACHE DICT HAS {entrycnt} ENTRIES{entrycnt > 0 and ':' or ''}")
    if entrycnt > 0:
        print("")
        pprint(instance, indent=4, depth=20,
                         width=width)
    print("")

def print_config(conf):
    """ Print debug information for a halogen.config.ConfigBase subclass """
    
    width: int = terminal_size().width
    
    print("=" * width)
    print("")
    print(f" • CONFIG: {conf.name}")
    print(f" • PREFIX: {conf.prefix}")
    print("")
    print("-" * width)
    
    print(" • INCLUDES:")
    print("")
    print(conf.get_includes())
    print("")
    print("-" * width)
    
    print(" • LIBS:")
    print("")
    print(conf.get_libs())
    print("")
    print("-" * width)
    
    print(" • CFLAGS:")
    print("")
    print(conf.get_cflags())
    print("")
    print("-" * width)
    
    print(" • LDFLAGS:")
    print("")
    print(conf.get_ldflags())
    print("")
    print("-" * width)
    
    print(" » stringification:")
    print("")
    print(str(conf))
    print("")
    # print("-" * width)

def test_compile(conf, test_source: str, print_cdb: bool = False) -> bool:
    """ Test-compile some inline C++ source, using the options provided
        by a given halogen.config.ConfigBase subclass instance.
    """
    import os
    import config
    from compiledb import CDBBase
    from filesystem import NamedTemporaryFile, TemporaryName
    
    width: int = terminal_size().width
    bytelength: int = len(test_source)
    output: tx.Tuple[str, ...] = tuple()
    px: str = "yodogg-"
    cdb: CDBBase = CDBBase()
    
    print("=" * width)
    print("")
    print(f" • TESTING COMPILATION: config.CXX({conf.name}, "
           "<out>, <in>, cdb=CDBBase()) ...")
    print("")
    
    with NamedTemporaryFile(suffix="cpp",
                            prefix=px) as tf:
        
        tf.file.write(test_source)
        tf.file.flush()
        
        with TemporaryName(suffix="cpp.o",
                           prefix=px,
                           randomized=True) as adotout:
            
            print(f" ≠ C++ SOURCE: {tf.name} ({bytelength}b)")
            print(f" ≠ C++ TARGET: {adotout.name}")
            print("")
            
            output += config.CXX(conf, outfile=os.fspath(adotout),
                                       infile=os.fspath(tf),
                                       cdb=cdb,
                                       verbose=True)
            
            print("-" * width)
            
            if len(output[1]) > 0:
                # failure
                print(" * COMPILATION FAILED:")
                stdout: str = u8str(output[0]).strip()
                stderr: str = u8str(output[1]).strip()
                if stdout:
                    print(f"STDOUT: {stdout}", file=sys.stdout)
                    print("")
                if stderr:
                    print(f"STDERR: {stderr}", file=sys.stderr)
                    print("")
                return False
            
            # success!
            print(" • COMPILATION TOTALLY WORKED!")
            print("")
            cdb_json: str = str(cdb)
            stdout: str = u8str(output[0]).strip()
            stderr: str = u8str(output[1]).strip()
            if cdb_json and print_cdb:
                print(f"   CDB: {cdb_json}", file=sys.stdout)
                print("")
            if stdout:
                print(f" » STDOUT: {stdout}", file=sys.stdout)
                print("")
            if stderr:
                print(f" » STDERR: {stderr}", file=sys.stderr)
                print("")
            if adotout.exists:
                return True
            else:
                print("... BUT THEN WHERE THE FUCK IS MY SHIT?!?!")
    return False

def test():
    import os
    from pprint import pformat
    
    print(f"PACKAGE: {__package__}")
    # print(f" MODULE: {__module__})")
    print(f"   FILE: {__file__}")
    print(f"   SPEC: {__spec__}")
    relfile: str = os.path.relpath('/Users/fish/Dropbox/halogen/halogen/filesystem.py',
                                    start=os.path.dirname(__file__))
    print(f"RELFILE: {relfile}")
    
    ns = {
             'func' : lambda: print("Yo Dogg"),
        'otherfunc' : lambda string=None: print(string or 'no dogg.'),
          # '__all__' : ('func', 'otherfunc'),
          # '__dir__' : lambda: ['func', 'otherfunc']
    }
    
    modulize(ns, 'wat', "WHAT THE HELL PEOPLE", __file__)
    import wat
    
    # Call module functions:
    wat.func()
    wat.otherfunc("Oh, Dogg!")
    
    # Inspect module:
    # contents = ", ".join(sorted(wat.__dict__.keys()))
    contents: str = pformat(wat.__dict__, indent=4, width=terminal_size().width)
    print(f"Imported module name:      {wat.__name__}")
    print(f"Imported module contents:  {contents}")
    print(f"Imported module docstring: {wat.__doc__}")

if __name__ == '__main__':
    test()
