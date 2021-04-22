#!/usr/bin/env python
import setuptools

from saika.const import Const

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()

setuptools.setup(
    name="Saika",
    version=Const.version,
    author="HsOjo",
    author_email="hsojo@qq.com",
    keywords='hsojo python3 flask web',
    description='''A simple web framework base on Flask.''',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/HsOjo/Saika/",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    python_requires='>=3.6',
    install_requires=requirements,
)
