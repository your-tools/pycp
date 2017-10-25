#!//bin/bash
set -e
echo "pycodestyle"
pycodestyle .
echo "pyflakes"
pyflakes $(find pycp -name "*.py")
echo "pylint"
pylint pycp
pytest
