#!/usr/bin/env python

import re
from setuptools import setup
from pip.req import parse_requirements

with open('navopt_admin/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='navopt-admin',
    version=version,
    license='proprietary',
    packages=[
        'navopt_admin',
    ],
    install_requires=reqs,
    entry_points={
        'console_scripts': [
            'navopt-admin = navopt_admin.cli:cli',
        ],
    }
)
