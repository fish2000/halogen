

class Install(object):
    
    def __init__(self, cmd='imread-config --prefix'):
        self.prefix = '/usr/local'
        out, err, ret = gosub(cmd, on_err=False)
        if ret == 0:
            self.prefix = out.strip()
        if out == '':
            # `imread-config --prefix` failed
            raise IOError("command `%s` failed" % cmd)
    
    def bin(self):
        import os
        return os.path.join(self.prefix, "bin")
    
    def include(self):
        import os
        return os.path.join(self.prefix, "include")
    
    def lib(self):
        import os
        return os.path.join(self.prefix, "lib")
    
    def dependency(self, name):
        import os
        return os.path.join(self.prefix, "include", name)

class HomebrewInstall(Install):
    
    def __init__(self, brew_name):
        cmd = "brew --prefix %s" % brew_name
        super(HomebrewInstall, self).__init__(cmd)


# What we are going for is:

# TO COMPILE GENERATOR SOURCE (AS BEFORE, BUT SANS `GenGen.cpp`):
#
# clang -fno-strict-aliasing -fno-common -dynamic -g -O2 -DNDEBUG -g -fwrapv -O3 -Wall -Wstrict-prototypes
# -I/usr/local/include -I/usr/local/opt/openssl/include -I/usr/local/opt/sqlite/include
# -I/usr/local/Cellar/python/2.7.12/Frameworks/Python.framework/Versions/2.7/include/python2.7
# -c ./generators/lesson_16_rgb_generate.cpp -o build/temp.macosx-10.11-x86_64-2.7/./generators/lesson_16_rgb_generate.o 
# -Wno-unused-function -Wno-unneeded-internal-declaration
# -O3 -fno-rtti -funroll-loops -mtune=native -std=c++1z -stdlib=libc++
#
# ... note that this generally sucks (-O2 and then two -O3 flags?!) but should probably
#     favor suckitude-preservation over suck-optimization; likely it will be derived from
#     whatever `python-config --cflags` barfs up. Halide include directory should either
#     be explicitly specified (to, like, the function or whatever that does this) or
#     maybe use `brew --prefix halide` if possible -- or maybe not, I don't fucking know,
#     why don't you just tell me MIISSSSSSTER SYSADMIN

class Generator(object):
    
    def compile(self, halide_prefix=None):


# TO LINK A COMPILED GENERATOR AS A DYNAMIC LIBRARY:
#
# clang++ -bundle -undefined dynamic_lookup build/temp.macosx-10.11-x86_64-2.7/hal/api.o 
# build/temp.macosx-10.11-x86_64-2.7/./generators/lesson_15_generators.o 
# build/temp.macosx-10.11-x86_64-2.7/./generators/lesson_16_rgb_generate.o
# -L/usr/local/lib -L/usr/local/opt/openssl/lib -L/usr/local/opt/sqlite/lib
# -o /Users/fish/Dropbox/halogen/hal/api.so -lHalide
#
# ... note that in this case there is unnecessary shit and it should be winnowed down --
#     but this is generally simpler, it is basically this:
#       {CC} {flags} generator.o -o generator.dylib -lHalide -L/where/libDalide/is/at
#     ... where fortunately {flags} are relatively simple, something like e.g.
#     “-bundle -undefined dynamic_lookup” (as above), with possibly an addendum to
#     adjust the @rpath as needed.