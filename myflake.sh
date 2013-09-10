#!/bin/sh

CMD=flake8-python2

$CMD setup.py
$CMD `find cptsoul -name '*.py'`
