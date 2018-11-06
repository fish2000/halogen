# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import os.path
import sys

# import before Cython stuff, to avoid
# overriding Cython’s Extension class:
from psutil import cpu_count                    # type: ignore
from setuptools import setup, find_packages     # type: ignore
from distutils.sysconfig import get_python_inc
from Cython.Distutils import Extension          # type: ignore
from Cython.Build import cythonize              # type: ignore

try:
    import numpy # type: ignore
except ImportError:
    class FakeNumpy(object):
        def get_include(self):
            return os.path.curdir
    numpy = FakeNumpy()
    print("import: NUMPY NOT FOUND (using shim)")
else:
    print(f"import: module {numpy.__name__} found")

try:
    import pythran # type: ignore
except ImportError:
    print("import: PYTHRAN NOT FOUND")
else:
    print(f"import: module {pythran.__name__} found")

sys.path.append(os.path.abspath(
                os.path.join(
                os.path.dirname(__file__), 'halogen')))

from halogen.config import Macros

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

api_extension_sources = [os.path.join('halogen', 'api.pyx')]
haldol_source_names = ('detail.cc', 'gil.cc', 'structcode.cc', 'terminal.cc', 'typecode.cc')
haldol_sources = [os.path.join('haldol', source) for source in haldol_source_names]

halogen_base_path = os.path.abspath(os.path.dirname('halogen'))

include_dirs = [
    get_python_inc(plat_specific=True),
    numpy.get_include(), # type: ignore
    halogen_base_path,
    os.path.join(halogen_base_path, 'ext'),
    # os.path.join(halogen_base_path, 'ext', 'halide'),
    # os.path.join(halogen_base_path, 'ext', 'haldol'),
    # os.path.join(halogen_base_path, 'ext', 'libcpp'),
    os.path.abspath(os.path.join('haldol', 'include')),
    os.path.curdir]

macros = Macros()
macros.define('NDEBUG')
macros.define('NUMPY')
macros.define('VERSION',                 __version__)
macros.define('NPY_NO_DEPRECATED_API',  'NPY_1_7_API_VERSION')
macros.define('PY_ARRAY_UNIQUE_SYMBOL', 'YO_DOGG_I_HEARD_YOU_LIKE_UNIQUE_SYMBOLS')

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
        'haldol'    : 'haldol',
        'halogen'   : 'halogen'
    },
    package_data=dict(),
    test_suite='nose.collector',
    ext_modules=cythonize([                 # type: ignore
        Extension('halogen.api',            # type: ignore
            api_extension_sources + haldol_sources,
            language="c++",
            include_dirs=[d for d in include_dirs if os.path.isdir(d)],
            define_macros=macros.to_list(),
            extra_link_args=[
                '-lHalide'],
            extra_compile_args=[
                '-Wno-unused-function',
                '-Wno-unneeded-internal-declaration',
                '-O3',
                '-fstrict-aliasing',
                '-funroll-loops',
                '-mtune=native',
                '-std=c++17',
                '-stdlib=libc++']
        )],
        nthreads=cpu_count(),
        compiler_directives=dict(language_level=2,
                                 infer_types=True,
                                 embedsignature=True)
    )
)
