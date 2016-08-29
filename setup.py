
from distutils.core import setup
# from distutils.extension import Extension
from Cython.Distutils import Extension
from Cython.Build import cythonize
import os

generators = []
# generator_dir = os.path.abspath('./generators')
generator_dir = './generators'
for dirpath, dirnames, filenames in os.walk(generator_dir):
    for filename in filenames:
        if filename.endswith('.cpp'):
            generators.append(os.path.join(dirpath, filename))

api_extension_sources = ['hal/api.pyx']
api_extension_sources.extend(generators)

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
