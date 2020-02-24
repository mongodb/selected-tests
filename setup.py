#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from glob import glob
from os.path import basename, splitext

from setuptools import find_packages, setup

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
        'Click==7.0',
        'GitPython==3.0.8',
        'boltons==19.1.0',
        'dnspython==1.16.0',
        'evergreen.py==1.0.2',
        "fastapi==0.45",
        'misc-utils-py == 0.1.2',
        'pymongo[tls]==3.8.0',
        'pytz==2019.3',
        'structlog==19.1.0',
        "uvicorn==0.10.8",
    ],
    entry_points={
        'console_scripts': [
            'selected-tests-service = selectedtests.app.app:main',
            'task-mappings = selectedtests.task_mappings.task_mappings_cli:main',
            'test-mappings = selectedtests.test_mappings.test_mappings_cli:main',
            'init-mongo = selectedtests.datasource.datasource_cli:main',
            'work-items = selectedtests.work_items.work_items_cli:main',
        ],
    },
    python_requires=">=3",
)
