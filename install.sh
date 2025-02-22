#!/bin/bash

set -eou pipefail

CWD="$(pwd)"

mkdir -p deps

# DAMI - TODO: investigate
# (daseg) dkazeem@c01:~/Projects/daseg$ ./install.sh
# Cloning into 'deps/swda'...
# remote: Enumerating objects: 72, done.
# remote: Counting objects: 100% (13/13), done.
# remote: Compressing objects: 100% (10/10), done.
# remote: Total 72 (delta 6), reused 9 (delta 3), pack-reused 59
# Unpacking objects: 100% (72/72), done.
# fatal: missing blob object '7db25bdd615b785b697d12f09afb2ea39de95105'
# fatal: remote did not send all necessary objects

# Obtain the swda repo and make it a detectable python package
if [ ! -d deps/swda ]; then
  git clone https://github.com/cgpotts/swda.git deps/swda
  cat <<EOM >deps/swda/setup.py
from setuptools import setup, find_packages
setup(
    name='swda',
    version='1.0',
    packages=find_packages(),
)
EOM
  cd deps/swda
  pip install -e .
  unzip swda.zip
  cd "$CWD"
fi

# Obtain the mrda repo and make it a detectable python package
if [ ! -d deps/mrda ]; then
  git clone https://github.com/NathanDuran/MRDA-Corpus deps/mrda
  cd deps/mrda
  mkdir mrda
  mv *.py mrda/
  touch __init__.py
  touch mrda/__init__.py
  cat <<EOM >setup.py
from setuptools import setup, find_packages
setup(
    name='mrda',
    version='1.0',
    packages=find_packages(),
)
EOM
  pip install -e .
  cd "$CWD"
fi

# Grab a spacy model
python -m spacy download en_core_web_sm
