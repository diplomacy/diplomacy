# ==============================================================================
# Copyright (C) 2019 - Philip Paquette
#
#  This program is free software: you can redistribute it and/or modify it under
#  the terms of the GNU Affero General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
#  details.
#
#  You should have received a copy of the GNU Affero General Public License along
#  with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==============================================================================
""" Package installer """
import sys
from setuptools import setup, find_packages

# Requiring python 3.5+.
# To simplify code for Tornado coroutines return statements, we don't support Python 3.4
# ( more info here: http://www.tornadoweb.org/en/stable/guide/coroutines.html#coroutines ).
if (sys.version_info.major, sys.version_info.minor) <= (3, 4):
    print("This package is only compatible with Python 3.5+, but you are running Python {}.{}."
          .format(sys.version_info.major, sys.version_info.minor))

# ------------------------------------
# Configuration
PACKAGE_NAME = 'diplomacy'
PACKAGE_VERSION = '1.1.0'

setup(name=PACKAGE_NAME,
      version=PACKAGE_VERSION,
      author='Philip Paquette',
      author_email='pcpaquette@gmail.com',
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'bcrypt',
          'coloredlogs',
          'python-dateutil',
          'pytz',
          'tornado>=5.0',
          'tqdm',
          'ujson',
      ],
      tests_require=['pytest'],
      classifiers=['License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7',
                   'Topic :: Games/Entertainment :: Board Games'])

# ------------------------------------
