#!/usr/bin/env python3

from setuptools import find_packages
from distutils.core import setup

setup(
    name="chitter",
    version="0.1",
    packages=find_packages(exclude=['env', 'tests']),
    include_package_data=True,
    install_requires=[
        "gevent",
        "flask",
        "requests",
        "redis",
    ],
    tests_require=['mock', 'nose'],
    test_suite='nose.collector',
)
