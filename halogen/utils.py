# -*- coding: utf-8 -*-

from __future__ import print_function

# get_terminal_size(): does what you think it does
# adapted from this: http://stackoverflow.com/a/566752/298171
def get_terminal_size(default_LINES=25, default_COLUMNS=80):
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

def terminal_print(message, color='red', asterisk='*'):
    """ Print a string to the terminal, centered and bookended with asterisks """
    from clint.textui.colored import red
    from clint.textui import colored
    colorizer = getattr(colored, color.lower(), red)
    message = " %s " % message.strip()
    asterisks = (terminal_width / 2) - (len(message) / 2)
    print(colorizer("""%(aa)s%(message)s%(ab)s""" % dict(
        aa=asterisk[0] * asterisks,
        ab=asterisk[0] * (asterisks + 0 - (len(message) % 2)),
        message=message)))

def print_config(conf):
    print("INCLUDES:")
    print("")
    print(conf.get_includes())
    print("")
    print("-" * terminal_width)
    
    print("LIBS:")
    print("")
    print(conf.get_libs())
    print("")
    print("-" * terminal_width)
    
    print("CFLAGS:")
    print("")
    print(conf.get_cflags())
    print("")
    print("-" * terminal_width)
    
    print("LDFLAGS:")
    print("")
    print(conf.get_ldflags())
    print("")
    # print("-" * terminal_width)

def test_compile(conf, test_source):
    import sys, os
    from config import CXX
    from tempfile import NamedTemporaryFile, mktemp
    
    output = tuple()
    px = "yodogg-"
    
    with NamedTemporaryFile(suffix=".cpp", prefix=px) as tf:
        tf.file.write(test_source)
        tf.file.flush()
        adotout = mktemp(suffix=".cpp.o", prefix=px)
        
        print("C++ SOURCE: %s" % tf.name)
        print("C++ TARGET: %s" % adotout)
        
        output += CXX(conf, adotout, tf.name, verbose=True)
        
        print("-" * terminal_width)
        
        if len(output[1]) > 0:
            # failure
            print("COMPILATION FAILED:")
            print(output[0], file=sys.stdout)
            print(output[1], file=sys.stderr)
            if os.path.exists(adotout):
                os.unlink(adotout)
            return
        
        # success!
        print("COMPILATION TOTALLY WORKED!")
        print(output[0], file=sys.stdout)
        print(output[1], file=sys.stderr)
        if os.path.exists(adotout):
            # another = os.path.basename(mktemp(suffix=".cpp.o", prefix=px))
            # shutil.copy2(adotout, "/tmp/%s" % another)
            os.unlink(adotout)
        else:
            print("... BUT THEN WHERE THE FUCK IS MY SHIT?!?!")