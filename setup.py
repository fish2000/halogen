
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

setup(
    ext_modules=cythonize([Extension('hal.api', ['hal/api.pyx'],
        extra_link_args=[
            '-lHalide'
        ],
        extra_compile_args=[
            '-O3',
            '-funroll-loops',
            '-mtune=native',
            '-std=c++1z',
            '-stdlib=libc++'
        ])
    ])
)
