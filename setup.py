"""
Copyright (C) 2013, 2014, 2015, 2016 Digital Freedom Foundation
  This file is part of GNUKhata:A modular,robust and Free Accounting System.

  GNUKhata is Free Software; you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as
  published by the Free Software Foundation; either version 3 of
  the License, or (at your option) any later version.and old.stockflag = 's'

  GNUKhata is distributed in the hope that it will be useful, but
  WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License along with GNUKhata (COPYING); if not, write to the
  Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
  Boston, MA  02110-1301  USA59 Temple Place, Suite 330,


Contributors:
"Krishnakant Mane" <kk@gmail.com>
"Ishan Masdekar " <imasdekar@dff.org.in>
"Navin Karkera" <navin@dff.org.in>
"""

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md")) as f:
    README = f.read()

requires = [
    "pyramid == 1.10.5",
    "psycopg2 == 2.9.1",  # previously 2.8.6
    "requests == 2.25.0",
    "sqlalchemy == 1.3.20",
    "monthdelta == 0.9.1",
    "pyjwt == 1.7.1",
    "pycryptodome == 3.9.9",
    "supervisor == 4.2.1",
    "natsort == 7.1.0",
    "gunicorn==20.1.0",
    "pillow == 8.0.1",
    "wsgicors == 0.7.0",
    "openpyxl == 2.5.0",
    "black == 21.6b0",
]

setup(
    name="gkcore",
    version=0.1,
    description="gkcore",
    long_description=README,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    keywords="web services",
    author="GNUKhata Team",
    author_email="",
    url="https://gnukhata.in",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    entry_points="""\
      [paste.app_factory]
      main=gkcore:main
      """,
    paster_plugins=["pyramid"],
)
