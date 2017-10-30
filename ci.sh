#!//bin/bash
set -e
echo "pycodestyle"
pycodestyle .
echo "pyflakes"
pyflakes $(find pycp test -name "*.py")
echo "mccabe"
python run-mccabe.py 15
echo "pylint"
pylint pycp
pytest
