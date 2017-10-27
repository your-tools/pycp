#!//bin/bash
set -e
echo "pycodestyle"
pycodestyle .
echo "pyflakes"
pyflakes $(find pycp -name "*.py")
echo "mccabe"
python run-mccabe.py 10
echo "pylint"
pylint pycp
pytest
