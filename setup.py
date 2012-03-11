from setuptools import setup, find_packages

setup(
      name='BicycleID',
      version='0.1.0dev',
      author='Jason Keith Moore',
      author_email='moorepants@gmail.com',
      packages=find_packages(),
      license='LICENSE.txt',
      description='''Visualization tool for bicycle system identification data.''',
      long_description=open('README.rst').read()
)
