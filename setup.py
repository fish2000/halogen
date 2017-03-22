
from __future__ import print_function

import os
from distutils.core import setup
from distutils.sysconfig import get_python_inc
from Cython.Distutils import Extension
from Cython.Build import cythonize

try:
    import numpy
except ImportError:
    class FakeNumpy(object):
        def get_include(self):
            return "."
    numpy = FakeNumpy()
    print("NUMPY NOT FOUND (using shim)")
else:
    print("import: module %s found" % numpy.__name__)

# VERSION & METADATA
__version__ = "<undefined>"
exec(compile(
    open(os.path.join(
        os.path.dirname(__file__),
        '__version__.py')).read(),
        '__version__.py', 'exec'))

# api_extension_sources = ['hal/api.pyx', 'generators/lesson_15_generators.cpp', 'generators/lesson_16_rgb_generate.cpp']
api_extension_sources = ['hal/api.pyx']
haldol_source_names = ('detail.cc', 'gil.cc', 'structcode.cc', 'typecode.cc')
haldol_sources = [os.path.join('haldol', source) for source in haldol_source_names]

build_with_numpy = False
include_dirs = [
    get_python_inc(plat_specific=1),
    numpy.get_include(),
    'haldol/include']

define_macros = []
define_macros.append(
    ('VERSION', __version__))
define_macros.append(
    ('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION'))
define_macros.append(
    ('PY_ARRAY_UNIQUE_SYMBOL', 'YO_DOGG_I_HEARD_YOU_LIKE_UNIQUE_SYMBOLS'))


setup(
    ext_modules=cythonize([
        Extension('hal.api',
            api_extension_sources +
            haldol_sources,
        include_dirs=include_dirs,
        define_macros=define_macros,
        extra_link_args=[
            '-lHalide'],
        extra_compile_args=[
            '-Wno-unused-function',
            '-Wno-unneeded-internal-declaration',
            '-O3',
            '-fno-rtti',
            '-funroll-loops',
            '-mtune=native',
            '-std=c++1z',
            '-stdlib=libc++']
        )
    ])
)
