# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

INSTALL_REQUIRES = []
with open(os.path.join(here, 'requirements.txt')) as req:
    INSTALL_REQUIRES = [req.read().split('\n')]

TESTS_REQUIRE = ['nose']
TESTING_REQUIRE = TESTS_REQUIRE + []

setup(name='Callisto',
      version='1.0',
      description='Remote control service for Cable TV STB',
      url='https://aoisakura.jp',
      author='Wataru Sakurai',
      author_email='wataru@aoisakura.jp',
      license='MIT',
      packages=find_packages(),
      install_requires=INSTALL_REQUIRES,
      zip_safe=False,
      entry_points={
      },
      extras_require={
          'develop': ['pep8'],
          'testing': TESTING_REQUIRE,
      },
      tests_require=TESTS_REQUIRE,
      test_suite='nose.collector',
      long_description='Remote control service for Cable TV STB',
      platforms=['POSIX'],
      classifiers=[
            'Environment :: Server',
            'Programming Language :: Python :: 3',
            'Operating System :: POSIX'])

