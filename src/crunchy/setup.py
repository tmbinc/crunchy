from distutils.core import setup
setup(name='crunchy',
      version='1.0',
      package_dir={'crunchy': ''},
      packages=['crunchy', 'crunchy.server', 'crunchy.core', 'crunchy.client', 'crunchy.fpga'],
      )
