from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()
with codecs.open(os.path.join(here, "LICENSE"), encoding="utf-8") as fh:
    license = "\n" + fh.read()

VERSION = '0.0.1a'
DESCRIPTION = 'Python package for creating DIY printers'

# Setting up
setup(
    name="rfc2911",
    version=VERSION,
    author="LIZARD-OFFICIAL-77",
    author_email="<lizard.official.77@gmail.com>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=(
        "requests",
    ),
    keywords=[
        'printer',
        'open-source',
        'foss',
        'lizard64'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2',
        'Programming Language :: Python :: 3 :: Only',
        'Operating System :: POSIX :: Linux',
    ],
    license=license,
    project_urls={
        'Source Code': 'https://github.com/lizard-64/PyRFC2911',  # GitHub link
        'Bug Tracker': 'https://github.com/lizard-64/PyRFC2911/issues',  # Link to issue tracker
    },
    url = "https://github.com/lizard-64/PyRFC2911"
)