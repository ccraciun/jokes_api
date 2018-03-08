#!/usr/bin/env python2

from setuptools import find_packages
from distutils.core import setup

setup(
    name="jokes",
    version="0.1",
    packages=find_packages(exclude=['env', 'tests']),
    include_package_data=True,
    install_requires=[
        "gevent",
        "flask",
        "requests",
        "redis",
        ],
    entry_points={
        'console_scripts': [
            'jokes=app.app:main',
            ],
        },
    tests_require=['mock', 'nose'],
    test_suite='nose.collector',
    )
