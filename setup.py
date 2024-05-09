"""
.. module:: setup.py

setup.py
******

:Description: setup.py

    Different Auxiliary functions used for different purposes

:Authors:
    bejar

:Version: 

:Date:  10/08/2020
"""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="owl2else", # Replace with your own username
    version="0.9.5",
    author="Javier Bejar",
    author_email="bejar@cs.upc.edu",
    description="Utilities to transform ontology OWL2 files to other formats",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bejar/owl2else",
    packages=['owl2conv'],
    scripts=['bin/owl2clips', 'bin/owl2rdflib', 'bin/owl2plot', 
             'bin/owl2clips.bat', 'bin/owl2rdflib.bat', 'bin/owl2plot.bat'],
    install_requires=['rdflib', 'matplotlib', 'graphviz'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
