#!/bin/sh
mkdir tmp
cd tmp
../setup.py sdist bdist_egg upload
cd ..
rm -r tmp
