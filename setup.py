from distutils.core import setup, Extension

setup(ext_modules=[Extension('render_c', sources=[
  'rendermodule.c',
  'rpi_ws281x/ws2811.c',
  'rpi_ws281x/mailbox.c',
  'rpi_ws281x/pwm.c',
  'rpi_ws281x/dma.c',
  'rpi_ws281x/rpihw.c'])])
