from setuptools import setup, find_packages

setup(name='meta_planning',
      version='1.0',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      install_requires=[
          'numpy'
      ]
      )