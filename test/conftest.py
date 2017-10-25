import os
import tempfile
import shutil

import pytest


@pytest.fixture()
def test_dir():
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    cur_test = os.path.join(cur_dir, "test_dir")
    temp_dir = tempfile.mkdtemp("pycp-test")
    test_dir = os.path.join(temp_dir, "test_dir")
    shutil.copytree(cur_test, test_dir)
    yield test_dir
    if os.environ.get("DEBUG"):
        print("not removing", test_dir)
    else:
        shutil.rmtree(test_dir)
