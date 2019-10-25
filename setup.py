#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='selectedtests',
    version='0.1.0',
    license='Apache License, Version 2.0',
    description='Calculate correlated tests for source files in a given evergreen project',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Lydia Stepanek',
    author_email='lydia.stepanek@mongodb.com',
    url='https://github.com/mongodb/selected-tests',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    install_requires=[
        'boltons==19.1.0',
        'Click==7.0',
        'evergreen.py==0.6.9',
        'flask==1.1.1',
        'flask-restplus==0.13.0',
        'GitPython==3.0.3',
        'structlog==19.1.0',
    ],
    entry_points={
        'console_scripts': [
            'selected-tests-service = selectedtests.app.app:main',
            'task-mappings = selectedtests.task_mappings.cli:main',
            'test-mappings = selectedtests.test_mappings.cli:main',
        ],
    }
)
