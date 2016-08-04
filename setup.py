from distutils.core import setup, Extension

setup(ext_modules=[Extension('render_c', sources=['render_c_module.c'])])
