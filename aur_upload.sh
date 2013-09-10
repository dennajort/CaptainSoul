#!/bin/sh
mkdir tmp
cd tmp
makepkg -p ../PKGBUILD --source
burp captainsoul-*.tar.gz
cd ..
rm -r tmp
