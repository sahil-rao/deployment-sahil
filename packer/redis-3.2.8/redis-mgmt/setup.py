#!/usr/bin/env python

import re
from setuptools import setup
from pip.req import parse_requirements

with open('redis_mgmt/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='redis-mgmt',
    version='0.1.0',
    license='proprietary',
    packages=['redis_mgmt'],
    install_requires=reqs,
    entry_points={
        'console_scripts': [
            'redis-sentinel-join-cluster = redis_mgmt.sentinel:join_cluster',
            'redis-server-join-cluster = redis_mgmt.server:join_cluster',
            'redis-server-is-master = redis_mgmt.server:is_master',
        ],
    }
)
