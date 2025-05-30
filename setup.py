#
# Blue Brain Nexus Forge is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Blue Brain Nexus Forge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Blue Brain Nexus Forge. If not, see <https://choosealicense.com/licenses/lgpl-3.0/>.

import os

from setuptools import find_packages, setup

HERE = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file.
with open(os.path.join(HERE, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="nexusforge",
    author="Blue Brain Project, EPFL",
    use_scm_version={
        "write_to": "kgforge/version.py",
        "write_to_template": "__version__ = '{version}'\n",
    },
    description="Building and Using Knowledge Graphs made easy.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    keywords="framework knowledge graph data science",
    url="https://github.com/BlueBrain/nexus-forge",
    packages=find_packages(),
    python_requires=">=3.8",
    setup_requires=["setuptools_scm"],
    install_requires=[
        "hjson",
        "pyyaml",
        "pandas",
        "puremagic",
        "aiohttp",
        "rdflib==7.0.0",
        "pyLD",
        "pyshacl==v0.25.0",
        "nest-asyncio>=1.5.1",
        "pyparsing>=2.0.2",
        "owlrl>=5.2.3",
        "elasticsearch_dsl==7.4.0",
        "requests==2.32.0",
        "typing-extensions",
        "jsonpath-ng"
    ],
    extras_require={
        "dev": [
            "tox",
            "pytest==7.3.0",
            "pytest-bdd==3.4.0",
            "pytest-cov",
            "pytest-mock",
        ],
        "docs": ["sphinx", "sphinx-bluebrain-theme"],
        "linking_sklearn": ["scikit-learn"],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Programming Language :: Python :: 3 :: Only",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    ],
)
