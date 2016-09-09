import os
from setuptools import setup, find_packages

from collectd_fluentd import __version__

HERE = os.path.dirname(__file__)
try:
    long_description = open(os.path.join(HERE, 'README.md')).read()
except:
    long_description = None

setup(
    name='collectd-fluentd',
    version=__version__,
    packages=find_packages(exclude=['test*']),
    install_requires=[
      'requests'
    ],
    tests_require=[
      'nose',
      'coverage',
      'mock',
      'flake8'
    ],

    author='Acquia Engineering',
    author_email='engineering@acquia.com',
    maintainer='Acquia Engineering <engineering@acquia.com>',
    url='https://github.com/acquia/collectd-fluentd',

    description='Fluentd plugin for collectd',
    long_description=long_description,
    license='Apache v2',
    keywords='collectd fluentd'
)
