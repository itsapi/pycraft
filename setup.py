from distutils.core import setup, Extension

setup(ext_modules=[Extension('render', sources=['rendermodule.c'])])
