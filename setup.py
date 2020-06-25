#!/usr/bin/env python

from setuptools import setup

classifiers = """\
Environment :: Console
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Operating System :: OS Independent
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: Implementation :: CPython
Programming Language :: Python :: Implementation :: PyPy
Development Status :: 4 - Beta
"""

setup(
    name='hformat',
    version='0.1.0',
    description='A human-understandable language for str.format',
    license='MIT',
    author_email='angelmorenoprieto@gmail.com',
    url='https://github.com/angmorpri/hformat',
    packages=['hformat'],
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    classifiers=classifiers.splitlines(),
    include_package_data=True,
)
