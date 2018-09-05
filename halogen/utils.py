# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import six
import sys
import typing as tx

from functools import wraps

__all__ = ('get_terminal_size', 'terminal_width',
                                'terminal_height',
           'tuplize',
           'wrap_value', 'Memoizer', 'memoize',
           'current_umask', 'masked_permissions',
           'append_paths', 'remove_paths',
           'string_types', 'is_string', 'stringify',
                                        'u8bytes',
                                        'u8str',
           'suffix_searcher',
           'terminal_print', 'print_cache',
                             'print_config',
                             'test_compile')

__dir__ = lambda: list(__all__)

# get_terminal_size(): does what you think it does
# adapted from this: http://stackoverflow.com/a/566752/298171

def get_terminal_size(default_LINES: int=25, default_COLUMNS: int=120):
    """ Get the width and height of the terminal window in characters """
    if hasattr(get_terminal_size, 'size_cache'):
        return get_terminal_size.size_cache[0], \
               get_terminal_size.size_cache[1]
    else:
        import os
        env = os.environ
        def ioctl_GWINSZ(fd):
            try:
                import fcntl, termios, struct
                cr = struct.unpack('hh',
                       fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            except:
                return
            return cr
        cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
        if not cr:
            try:
                fd = os.open(os.ctermid(), os.O_RDONLY)
                cr = ioctl_GWINSZ(fd)
                os.close(fd)
            except:
                pass
        if not cr:
            cr = (env.get('LINES',   default_LINES),
                  env.get('COLUMNS', default_COLUMNS))
        get_terminal_size.size_cache = (int(cr[1]), int(cr[0]))
    return get_terminal_size.size_cache[0], \
           get_terminal_size.size_cache[1]

terminal_width, terminal_height = get_terminal_size()

string_types = (type(''),
                type(b''),
                type(r''),
                type(u'')) + six.string_types

is_string = lambda thing: isinstance(thing, string_types)

def tuplize(*items) -> tuple:
    return tuple(item for item in items if item is not None)

def listify(*items) -> list:
    return list(item for item in items if item is not None)

def wrap_value(value):
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

def append_paths(*putatives):
    """ Mutate `sys.path` by appending one or more new paths -- all of which
        are checked for both nonexistence and presence within the existing
        `sys.path` list via inode lookup, and which those failing such checks
        are summarily excluded.
    """
    import os
    out = {}
    if len(putatives) < 1:
        return out
    paths = set(sys.path)
    append_paths.oldsyspath = tuple(sys.path)
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

append_paths.oldsyspath = tuple()

def remove_paths(*putatives):
    """ Mutate `sys.path` by removing one or more existing paths --
        all of which are checked for presence within the existing `sys.path`
        list via inode lookup before being marked for removal, which that
        (the removal) is done atomically.
    """
    import os
    out = {}
    if len(putatives) < 1:
        return out
    removals = set()
    paths = set(sys.path)
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
    remove_paths.oldsyspath = tuple(sys.path)
    sys.path = list(paths)
    return out

remove_paths.oldsyspath = tuple()

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

def stringify(instance, fields):
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
    field_dict = {}
    for field in fields:
        field_value = getattr(instance, field, "")
        field_value = callable(field_value) and field_value() or field_value
        if field_value:
            field_dict.update({ str(field) : field_value })
    field_dict_items = []
    for k, v in field_dict.items():
        field_dict_items.append(f'''{k}="{v}"''')
    typename = type(instance).__name__
    field_dict_string = ", ".join(field_dict_items)
    hex_id = hex(id(instance))
    return f"{typename}({field_dict_string}) @ {hex_id}"

def suffix_searcher(suffix):
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
    regex_str = r""
    if suffix.startswith(os.extsep):
        regex_str += rf"\{suffix}$"
    else:
        regex_str += rf"\{os.extsep}{suffix}$"
    searcher = re.compile(regex_str, re.IGNORECASE).search
    return lambda searching_for: bool(searcher(searching_for))

def terminal_print(message: str, handle: tx.Any=sys.stdout,
                   color: str='red', asterisk: str='*'):
    """ Print a string to the terminal, centered and bookended with asterisks
    """
    from clint.textui.colored import red
    from clint.textui import colored
    
    colorizer = getattr(colored, color.lower(), red)
    message = f" {message.strip()} "
    
    asterisks = (terminal_width / 2) - (len(message) / 2)
    aa = asterisk[0] * asterisks
    ab = asterisk[0] * (asterisks + 0 - (len(message) % 2))
    
    print(colorizer(f"{aa}{message}{ab}"), file=handle)

def print_cache(BaseClass: type, cache_instance_name: str):
    """ Pretty-print the contents of a cached metaclass variable """
    from pprint import pprint
    
    instance = getattr(BaseClass, cache_instance_name)
    qualname = f"{BaseClass.__name__}.{cache_instance_name}"
    entrycnt = len(instance)
    dicttype = type(instance).__name__
    
    width, _ = get_terminal_size()
    
    print("=" * width)
    print("")
    print(f" • DUMPING METACLASS CACHE « {qualname}: {dicttype} »")
    print(f" • CACHE DICT HAS {entrycnt} ENTRIES{entrycnt > 0 and ':' or ''}")
    if entrycnt > 0:
        print("")
        pprint(instance, indent=4,
                         width=width)
    print("")

def print_config(conf):
    """ Print debug information for a halogen.config.ConfigBase subclass """
    
    width, _ = get_terminal_size()
    
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

def test_compile(conf, test_source, print_cdb=False):
    """ Test-compile some inline C++ source, using the options provided
        by a given halogen.config.ConfigBase subclass instance.
    """
    import os
    import config
    from compiledb import CDBBase
    from filesystem import NamedTemporaryFile, TemporaryName
    
    width, _ = get_terminal_size()
    bytelength = len(test_source)
    output = tuple()
    px = "yodogg-"
    cdb = CDBBase()
    
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
                                       infile=tf.name,
                                       cdb=cdb,
                                       verbose=True)
            
            print("-" * width)
            
            if len(output[1]) > 0:
                # failure
                print(" * COMPILATION FAILED:")
                stdout = u8str(output[0]).strip()
                stderr = u8str(output[1]).strip()
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
            cdb_json = str(cdb)
            stdout = u8str(output[0]).strip()
            stderr = u8str(output[1]).strip()
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
