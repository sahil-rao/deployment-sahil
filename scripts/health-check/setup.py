#!/usr/bin/env python

import re
from setuptools import setup
from pip.req import parse_requirements

with open('health_check/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='health_check',
    version=version,
    license='proprietary',
    packages=[
        'health_check',
    ],
    install_requires=reqs,
    entry_points={
        'console_scripts': [
            'health-check = health_check.cli:cli',
        ],
    }
)
