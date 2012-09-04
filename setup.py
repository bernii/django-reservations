#!/usr/bin/env python

from setuptools import setup, find_packages
import os

PACKAGE_DIR = os.path.abspath(os.path.dirname(__file__))
os.chdir(PACKAGE_DIR)


setup(name='django-reservations',
      version=0.2,
      url='https://github.com/bernii/django-reservations',
      author="Bernard Kobos",
      author_email="bkobos@extensa.pl",
      description=("Django module for handling reservations/booking"),
      long_description=file(os.path.join(PACKAGE_DIR, 'README.md')).read(),
      license='WOW',
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'django>=1.4',
          ],
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: WOW License',
                   'Operating System :: Unix',
                   'Programming Language :: Python']
      )
