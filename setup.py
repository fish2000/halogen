
from distutils.core import setup
from Cython.Distutils import Extension
from Cython.Build import cythonize

api_extension_sources = ['hal/api.pyx']

setup(
    ext_modules=cythonize([
        Extension('hal.api',
            api_extension_sources,
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
