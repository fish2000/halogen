
from __future__ import print_function

import os
import os.path
from setuptools import setup, find_packages # import before Cython stuff, to avoid
                                            # overriding Cython’s Extension class.
from distutils.sysconfig import get_python_inc
from Cython.Distutils import Extension
from Cython.Build import cythonize

try:
    import numpy
except ImportError:
    class FakeNumpy(object):
        def get_include(self):
            return os.path.curdir
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

long_description = """ Cython-based alternative to Halide’s GenGen.cpp """

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Topic :: Multimedia',
    'Topic :: Scientific/Engineering :: Image Recognition',
    'Topic :: Software Development :: Libraries',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: C++',
    'License :: OSI Approved :: MIT License']

# api_extension_sources = [os.path.join('hal', 'api.pyx'),
#                          os.path.join('generators', 'lesson_15_generators.cpp'),
#                          os.path.join('generators', 'lesson_16_rgb_generate.cpp')]
api_extension_sources = [os.path.join('hal', 'api.pyx')]
haldol_source_names = ('detail.cc', 'gil.cc', 'structcode.cc', 'terminal.cc', 'typecode.cc')
haldol_sources = [os.path.join('haldol', source) for source in haldol_source_names]

include_dirs = [
    get_python_inc(plat_specific=1),
    numpy.get_include(),
    os.path.join('haldol', 'include'),
    os.path.curdir]

define_macros = []
define_macros.append(
    ('VERSION', __version__))
define_macros.append(
    ('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION'))
define_macros.append(
    ('PY_ARRAY_UNIQUE_SYMBOL', 'YO_DOGG_I_HEARD_YOU_LIKE_UNIQUE_SYMBOLS'))


setup(name='halide-halogen',
    version=__version__,
    description=long_description,
    long_description=long_description,
    author='Alexander Bohn',
    author_email='fish2000@gmail.com',
    license='MIT',
    platforms=['Any'],
    classifiers=classifiers,
    url='http://github.com/fish2000/halogen',
    packages=find_packages(),
    package_dir={
        'hal'       : 'hal',
        'haldol'    : 'haldol',
        'halogen'   : 'halogen'
    },
    package_data=dict(),
    test_suite='nose.collector',
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
                '-fstrict-aliasing',
                '-fno-rtti',
                '-funroll-loops',
                '-mtune=native',
                '-std=c++1z',
                '-stdlib=libc++']
        )]
    )
)
