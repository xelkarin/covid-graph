""" Setuptools build file """
from pathlib import Path

from setuptools import setup


setup(
    name="covid",
    py_modules=["covid"],
    entry_points={"console_scripts": ["covid=covid:main"]},
    setup_requires=["setuptools_scm"],
    use_scm_version=True,
    python_requires=">=3.6, <4'",
    author="Robert Gill and Carlos Meza",
    description="Graphing covid-19 state data.",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    license="BSD-2-Clause",
    url="https://github.com/xelkarin/covid-graph",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords=["covid-19", "coronavirus"],
)
