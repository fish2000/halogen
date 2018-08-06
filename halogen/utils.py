# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
from functools import wraps
import six

__all__ = ('get_terminal_size', 'terminal_width',
                                'terminal_height',
           'wrap_value', 'Memoizer', 'memoize',
           'current_umask', 'masked_permissions',
           'append_paths', 'remove_paths',
           'string_types', 'is_string', 'stringify',
                                        'u8bytes',
                                        'u8str',
           'suffix_searcher',
           'terminal_print', 'print_config',
                             'test_compile')

# get_terminal_size(): does what you think it does
# adapted from this: http://stackoverflow.com/a/566752/298171
def get_terminal_size(default_LINES=25, default_COLUMNS=120):
    """ Get the width and height of the terminal window in characters """
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
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
    return int(cr[1]), int(cr[0])

terminal_width, terminal_height = get_terminal_size()

string_types = (type(''),
                type(b''),
                type(r''),
                type(u'')) + six.string_types

is_string = lambda thing: isinstance(thing, string_types)

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
    """ Mutate `sys.path` by appending one or more new paths --
        all of which are checked for both nonexistence and presence
        within the existing `sys.path` list via inode lookup, and
        which those failing such checks are summarily excluded.
    """
    import sys, os
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
    """ Mutate `sys.path` by removing one or more new paths --
        all of which are checked for presence within the existing
        `sys.path` list via inode lookup before being marked for
        removal, which that (the removal) is done atomically.
    """
    import sys, os
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

def u8bytes(string_source):
    if type(string_source) == bytes:
        return string_source
    elif type(string_source) == str:
        return bytes(string_source, encoding='UTF-8')
    elif isinstance(string_source, six.string_types):
        return bytes(string_source, encoding='UTF-8')
    elif type(string_source) == bool:
        return string_source and b'True' or b'False'
    elif string_source is None:
        return b'None'
    return bytes(string_source)

def u8str(string_source):
    return u8bytes(string_source).decode('UTF-8')

def stringify(instance, fields):
    field_dict = {}
    for field in fields:
        field_value = getattr(instance, field, "")
        field_value = callable(field_value) and field_value() or field_value
        if field_value:
            field_dict.update({ str(field) : field_value })
    field_dict_items = []
    for k, v in field_dict.items():
        field_dict_items.append(f'''{k}="{v}"''')
    field_dict_string = ", ".join(field_dict_items)
    return f"{instance.__class__.__name__}({field_dict_string}) @ {hex(id(instance))}"

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

def terminal_print(message, color='red', asterisk='*'):
    """ Print a string to the terminal, centered and bookended with asterisks """
    from clint.textui.colored import red
    from clint.textui import colored
    colorizer = getattr(colored, color.lower(), red)
    message = f" {message.strip()} "
    asterisks = (terminal_width / 2) - (len(message) / 2)
    aa = asterisk[0] * asterisks
    ab = asterisk[0] * (asterisks + 0 - (len(message) % 2))
    print(colorizer(f"{aa}{message}{ab}"))

def print_config(conf):
    """ Print debug information for a halogen.config.ConfigBase subclass """
    
    width, height = get_terminal_size()
    
    print("=" * width)
    print("")
    print(f"CONFIG: {conf.name}")
    print(f"PREFIX: {conf.prefix}")
    print("")
    print("-" * width)
    
    print("INCLUDES:")
    print("")
    print(conf.get_includes())
    print("")
    print("-" * width)
    
    print("LIBS:")
    print("")
    print(conf.get_libs())
    print("")
    print("-" * width)
    
    print("CFLAGS:")
    print("")
    print(conf.get_cflags())
    print("")
    print("-" * width)
    
    print("LDFLAGS:")
    print("")
    print(conf.get_ldflags())
    print("")
    print("-" * width)
    
    print("stringification:")
    print("")
    print(str(conf))
    print("")
    # print("-" * width)
    

def test_compile(conf, test_source):
    """ Test-compile some inline C++ source, using the options provided
        by a given halogen.config.ConfigBase subclass instance.
    """
    
    import sys, os
    import config
    from filesystem import NamedTemporaryFile, TemporaryName
    
    width, height = get_terminal_size()
    output = tuple()
    px = "yodogg-"
    
    print("=" * width)
    print("")
    print(f"TESTING COMPILATION: config.CXX({conf.name}, <out>, <in>) ...")
    print("")
    
    with NamedTemporaryFile(suffix="cpp", prefix=px) as tf:
        tf.file.write(test_source)
        tf.file.flush()
        
        with TemporaryName(suffix="cpp.o", prefix=px) as adotout:
            print(f"C++ SOURCE: {tf.name}")
            print(f"C++ TARGET: {adotout.name}")
            
            output += config.CXX(conf, outfile=adotout.name,
                                       infile=tf.name,
                                       verbose=True)
            
            print("-" * width)
            
            if len(output[1]) > 0:
                # failure
                print("COMPILATION FAILED:")
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
            print("COMPILATION TOTALLY WORKED!")
            print("")
            stdout = u8str(output[0]).strip()
            stderr = u8str(output[1]).strip()
            if stdout:
                print(f"STDOUT: {stdout}", file=sys.stdout)
                print("")
            if stderr:
                print(f"STDERR: {stderr}", file=sys.stderr)
                print("")
            if os.path.exists(str(adotout)):
                return True
            else:
                print("... BUT THEN WHERE THE FUCK IS MY SHIT?!?!")
    return False
