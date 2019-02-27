#!//bin/bash
set -e
echo "pycodestyle"
dmenv run pycodestyle .
echo "pyflakes"
dmenv run pyflakes $(find pycp test -name "*.py")
echo "mccabe"
dmenv run python run-mccabe.py 15
echo "pylint"
dmenv run pylint pycp
dmenv run pytest
