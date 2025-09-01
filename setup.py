#!/usr/bin/env python

"""
vertopal-cli
~~~~~~~~~~~~

:copyright: (c) 2023 Vertopal - https://www.vertopal.com
:license: MIT, see LICENSE for more details.

https://github.com/vertopal/vertopal-cli
"""

from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="vertopal",
    version="2.0.3",
    description="Convert your files in terminal using Vertopal API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Vertopal",
    author_email="contact@vertopal.com",
    url="https://github.com/vertopal/vertopal-cli",
    packages=find_packages(where="src"),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
    ],
    keywords=[
        "convert",
        "file",
        "vertopal",
        "api",
        "converter",
    ],
    package_dir={"": "src"},
    project_urls={
        "Homepage": "https://www.vertopal.com",
        "Funding": "https://www.vertopal.com/en/donate",
        "Source": "https://github.com/vertopal/vertopal-cli",
        "Bug Tracker": "https://github.com/vertopal/vertopal-cli/issues",
    },
    entry_points={
        "console_scripts": [
            "vertopal=vertopal.vertopal:main",
        ],
    },
    install_requires=[
        "requests>=2.28.2",
    ],
    python_requires=">=3.9",
)
