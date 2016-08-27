from distutils.core import setup, Extension
import translate_data

with open('data.c', 'w') as data_file:
	print(translate_data.translate(), file=data_file)

setup(ext_modules=[Extension('render_c', sources=['render_c_module.c'])])
