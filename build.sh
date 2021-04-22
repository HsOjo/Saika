#!/bin/bash
rm -fr dist
python setup.py sdist bdist_wheel
rm -fr build *.egg-info
pip install dist/*.whl --upgrade

if [[ $1 = '--upload' ]]; then
  twine upload dist/*
fi
