"""Unit test for pycp

You can set environnent variable DEBUG to 1
to not remove temporary directories created during test.

(Useful for diagnostic)
"""

import unittest
import tempfile  # for mkdtemp
import shutil
import sys
import os
import stat
import time


import pycp
from pycp.main import main as pycp_main
from pycp.util import pprint_transfer


class CpTestCase(unittest.TestCase):
    def setUp(self):
        """Put some empty files and directories in a temporary
        directory

        """
        cur_dir = os.path.abspath(os.path.dirname(__file__))
        cur_test = os.path.join(cur_dir, "test_dir")
        temp_dir = tempfile.mkdtemp("pycp-test")
        self.test_dir = os.path.join(temp_dir, "test_dir")
        shutil.copytree(cur_test, self.test_dir)
        self.previous_dir = os.getcwd()

    def test_zero(self):
        sys.argv=["pycp"]
        self.assertRaises(SystemExit, pycp_main)

    def test_cp_self_1(self):
        "a_file -> a_file"
        a_file      = os.path.join(self.test_dir, "a_file")
        sys.argv = ["pycp", a_file, a_file]
        self.assertRaises(SystemExit, pycp_main)

    def test_cp_self_2(self):
        "a_file -> ."
        a_file      = os.path.join(self.test_dir, "a_file")
        sys.argv = ["pycp", a_file, self.test_dir]
        self.assertRaises(SystemExit, pycp_main)

    def test_cp_file_file(self):
        "a_file -> a_file.back"
        # cp a_file a_file.back
        a_file      = os.path.join(self.test_dir, "a_file")
        a_file_back = os.path.join(self.test_dir, "a_file.back")

        sys.argv = ["pycp", a_file, a_file_back]
        pycp_main()
        self.assertTrue(os.path.exists(a_file_back))

    def test_cp_symlink(self):
        # note: since shutil.copytree does not handle
        # symlinks the way we would like to, create
        # link now
        a_link = os.path.join(self.test_dir, "a_link")
        a_target = os.path.join(self.test_dir, "a_target")
        with open(a_target, "w") as fp:
            fp.write("a_target\n")
        os.symlink("a_target", a_link)
        b_link = os.path.join(self.test_dir, "b_link")
        sys.argv = ["pycp", a_link, b_link]
        pycp_main()
        self.assertTrue(os.path.islink(b_link))
        b_target = os.readlink(b_link)
        self.assertEquals(b_target, "a_target")

    def test_cp_keep_rel_symlink(self):
        a_link = os.path.join(self.test_dir, "a_link")
        a_target = os.path.join(self.test_dir, "a_target")
        with open(a_target, "w") as fp:
            fp.write("a_target\n")
        os.symlink("a_target", a_link)
        b_dir = os.path.join(self.test_dir, "b_dir")
        os.mkdir(b_dir)
        b_link = os.path.join(b_dir, "b_link")
        sys.argv = ["pycp", a_link, b_link]
        pycp_main()
        self.assertTrue(os.path.islink(b_link))
        b_target = os.readlink(b_link)
        self.assertEquals(b_target, "a_target")

    def test_cp_exe_file(self):
        "copied file should still be executable"
        exe_file   = os.path.join(self.test_dir, "file.exe")
        exe_file_2 = os.path.join(self.test_dir, "file2.exe")
        sys.argv = ["pycp", exe_file, exe_file_2]
        pycp_main()
        self.assertTrue(os.access(exe_file_2, os.X_OK))

    def test_cp_file_dir(self):
        "a_file -> b_dir"
        a_file = os.path.join(self.test_dir, "a_file")
        b_dir  = os.path.join(self.test_dir, "b_dir")
        os.mkdir(b_dir)
        sys.argv = ["pycp", a_file, b_dir]
        pycp_main()
        dest = os.path.join(b_dir, "a_file")
        self.assertTrue(os.path.exists(dest))

    def test_cp_dir_dir_1(self):
        "a_dir -> b_dir (b_dir does not exist)"
        a_dir = os.path.join(self.test_dir, "a_dir")
        b_dir = os.path.join(self.test_dir, "b_dir")
        sys.argv = ["pycp", a_dir, b_dir]
        pycp_main()
        c_file = os.path.join(b_dir, "c_file")
        d_file = os.path.join(b_dir, "c_file")
        self.assertTrue(os.path.exists(c_file))
        self.assertTrue(os.path.exists(d_file))

    def test_cp_dir_dir_2(self):
        "a_dir -> b_dir (b_dir exists)"
        a_dir = os.path.join(self.test_dir, "a_dir")
        b_dir = os.path.join(self.test_dir, "b_dir")
        os.mkdir(b_dir)
        sys.argv = ["pycp", a_dir, b_dir]
        pycp_main()
        c_file = os.path.join(b_dir, "a_dir", "c_file")
        d_file = os.path.join(b_dir, "a_dir", "c_file")
        self.assertTrue(os.path.exists(c_file))
        self.assertTrue(os.path.exists(d_file))

    def test_cp_dir_dir2_global(self):
        a_dir = os.path.join(self.test_dir, "a_dir")
        b_dir = os.path.join(self.test_dir, "b_dir")
        os.mkdir(b_dir)
        sys.argv = ["pycp", "-g", a_dir, b_dir]
        pycp_main()
        c_file = os.path.join(b_dir, "a_dir", "c_file")
        d_file = os.path.join(b_dir, "a_dir", "c_file")
        self.assertTrue(os.path.exists(c_file))
        self.assertTrue(os.path.exists(d_file))


    def test_no_source(self):
        "d_file -> d_file.back but d_file does not exists"
        d_file = os.path.join(self.test_dir, "d_file")
        sys.argv = ["pycp", d_file, "d_file.back"]
        self.assertRaises(SystemExit, pycp_main)


    def test_no_dest(self):
        "a_file -> d_dir but d_dir does not exists"
        a_file = os.path.join(self.test_dir, "a_file")
        d_dir  = os.path.join(self.test_dir, "d_dir" + os.path.sep)
        sys.argv = ["pycp", a_file, d_dir]
        self.assertRaises(SystemExit, pycp_main)


    def test_several_sources_1(self):
        "a_file b_file c_file"
        a_file = os.path.join(self.test_dir, "a_file")
        b_file = os.path.join(self.test_dir, "b_file")
        c_file = os.path.join(self.test_dir, "c_file")
        sys.argv = ["pycp", a_file, b_file, c_file]
        self.assertRaises(SystemExit, pycp_main)


    def test_several_sources_2(self):
        "a_file b_file c_dir but c_dir does not exists"
        a_file = os.path.join(self.test_dir, "a_file")
        b_file = os.path.join(self.test_dir, "b_file")
        c_dir  = os.path.join(self.test_dir, "c_dir" )
        sys.argv = ["pycp", a_file, b_file, c_dir]
        self.assertRaises(SystemExit, pycp_main)


    def test_overwrite_1(self):
        "a_file -> b_file and b_file already exists (unsafe)"
        a_file = os.path.join(self.test_dir, "a_file")
        b_file = os.path.join(self.test_dir, "b_file")
        sys.argv = ["pycp", a_file, b_file]
        pycp_main()
        b_file_desc = open(b_file, "r")
        b_contents  = b_file_desc.read()
        b_file_desc.close()
        self.assertEquals(b_contents, "a\n")


    def test_overwrite_2(self):
        "a_file -> b_file and b_file already exists (safe)"
        a_file = os.path.join(self.test_dir, "a_file")
        b_file = os.path.join(self.test_dir, "b_file")
        sys.argv = ["pycp", "--safe",  a_file, b_file]
        pycp_main()
        b_file_desc = open(b_file, "r")
        b_contents  = b_file_desc.read()
        b_file_desc.close()
        self.assertEquals(b_contents, "b\n")

    def test_copy_readonly(self):
        "a_file -> ro_dir but ro_dir is read only"
        a_file = os.path.join(self.test_dir, "a_file")
        ro_dir = tempfile.mkdtemp("pycp-test-ro")
        os.chmod(ro_dir, stat.S_IRUSR | stat.S_IXUSR)
        sys.argv = ["pycp", a_file, ro_dir]
        self.assertRaises(SystemExit, pycp_main)
        shutil.rmtree(ro_dir)

    def tearDown(self):
        """Remove the temporary directory

        """
        if os.environ.get("DEBUG"):
            print "not removing", self.test_dir
        else:
            shutil.rmtree(self.test_dir)


class MvTestCase(unittest.TestCase):
    def setUp(self):
        """Put some empty files and directories in a temporary
        directory

        """
        cur_dir = os.path.abspath(os.path.dirname(__file__))
        cur_test = os.path.join(cur_dir, "test_dir")
        temp_dir = tempfile.mkdtemp("pycp-test")
        self.test_dir = os.path.join(temp_dir, "test_dir")
        shutil.copytree(cur_test, self.test_dir)
        self.previous_dir = os.getcwd()

    def test_zero(self):
        sys.argv=["pymv"]
        self.assertRaises(SystemExit, pycp_main)


    def test_mv_self_1(self):
        "a_file -> a_file"
        a_file      = os.path.join(self.test_dir, "a_file")
        sys.argv = ["pymv", a_file, a_file]
        self.assertRaises(SystemExit, pycp_main)

    def test_mv_self_2(self):
        "a_file -> ."
        a_file      = os.path.join(self.test_dir, "a_file")
        sys.argv = ["pymv", a_file, self.test_dir]
        self.assertRaises(SystemExit, pycp_main)

    def test_mv_file_file(self):
        "a_file -> a_file.back"
        a_file      = os.path.join(self.test_dir, "a_file")
        a_file_back = os.path.join(self.test_dir, "a_file.back")

        sys.argv = ["pymv", a_file, a_file_back]
        pycp_main()
        self.assertTrue (os.path.exists(a_file_back))
        self.assertFalse(os.path.exists(a_file))


    def test_mv_file_dir(self):
        "a_file -> b_dir"
        a_file = os.path.join(self.test_dir, "a_file")
        b_dir  = os.path.join(self.test_dir, "b_dir")
        os.mkdir(b_dir)
        sys.argv = ["pymv", a_file, b_dir]
        pycp_main()
        dest = os.path.join(b_dir, "a_file")
        self.assertTrue (os.path.exists(dest))
        self.assertFalse(os.path.exists(a_file))


    def test_mv_dir_dir_1(self):
        "a_dir -> b_dir (b_dir does not exist)"
        a_dir = os.path.join(self.test_dir, "a_dir")
        b_dir = os.path.join(self.test_dir, "b_dir")
        sys.argv = ["pymv", a_dir, b_dir]
        pycp_main()
        c_file = os.path.join(b_dir, "c_file")
        d_file = os.path.join(b_dir, "c_file")
        self.assertTrue (os.path.exists(c_file))
        self.assertTrue (os.path.exists(d_file))
        self.assertFalse(os.path.exists(a_dir))

    def test_mv_dir_dir2_global(self):
        "a_dir -> b_dir (b_dir does not exist), with --global"
        a_dir = os.path.join(self.test_dir, "a_dir")
        b_dir = os.path.join(self.test_dir, "b_dir")
        sys.argv = ["pymv", a_dir, b_dir]
        pycp_main()
        c_file = os.path.join(b_dir, "c_file")
        d_file = os.path.join(b_dir, "c_file")
        self.assertTrue (os.path.exists(c_file))
        self.assertTrue (os.path.exists(d_file))
        self.assertFalse(os.path.exists(a_dir))

    def test_mv_dir_dir_2(self):
        "a_dir -> b_dir (b_dir exists)"
        a_dir = os.path.join(self.test_dir, "a_dir")
        b_dir = os.path.join(self.test_dir, "b_dir")
        os.mkdir(b_dir)
        sys.argv = ["pymv", a_dir, b_dir]
        pycp_main()
        c_file = os.path.join(b_dir, "a_dir", "c_file")
        d_file = os.path.join(b_dir, "a_dir", "c_file")
        self.assertTrue (os.path.exists(c_file))
        self.assertTrue (os.path.exists(d_file))
        self.assertFalse(os.path.exists(a_dir))

    def test_no_source(self):
        "d_file -> d_file.back but d_file does not exists"
        d_file = os.path.join(self.test_dir, "d_file")
        sys.argv = ["pymv", d_file, "d_file.back"]
        self.assertRaises(SystemExit, pycp_main)


    def test_no_dest(self):
        "a_file -> d_dir but d_dir does not exists"
        a_file = os.path.join(self.test_dir, "a_file")
        d_dir  = os.path.join(self.test_dir, "d_dir" + os.path.sep)
        sys.argv = ["pymv", a_file, d_dir]
        self.assertRaises(SystemExit, pycp_main)


    def test_several_sources_1(self):
        "a_file b_file c_file"
        a_file = os.path.join(self.test_dir, "a_file")
        b_file = os.path.join(self.test_dir, "b_file")
        c_file = os.path.join(self.test_dir, "c_file")
        sys.argv = ["pymv", a_file, b_file, c_file]
        self.assertRaises(SystemExit, pycp_main)


    def test_several_sources_2(self):
        "a_file b_file c_dir but c_dir does not exists"
        a_file = os.path.join(self.test_dir, "a_file")
        b_file = os.path.join(self.test_dir, "b_file")
        c_dir  = os.path.join(self.test_dir, "c_dir" )
        sys.argv = ["pymv", a_file, b_file, c_dir]
        self.assertRaises(SystemExit, pycp_main)


    def test_overwrite_1(self):
        "a_file -> b_file and b_file already exists (unsafe)"
        a_file = os.path.join(self.test_dir, "a_file")
        b_file = os.path.join(self.test_dir, "b_file")
        sys.argv = ["pymv", a_file, b_file]
        pycp_main()
        b_file_desc = open(b_file, "r")
        b_contents  = b_file_desc.read()
        b_file_desc.close()
        self.assertEquals(b_contents, "a\n")
        self.assertFalse(os.path.exists(a_file))


    def test_overwrite_2(self):
        "a_file -> b_file and b_file already exists (safe)"
        a_file = os.path.join(self.test_dir, "a_file")
        b_file = os.path.join(self.test_dir, "b_file")
        sys.argv = ["pymv", "--safe",  a_file, b_file]
        pycp_main()
        b_file_desc = open(b_file, "r")
        b_contents  = b_file_desc.read()
        b_file_desc.close()
        self.assertEquals(b_contents, "b\n")
        self.assertTrue(os.path.exists(a_file))

    def test_empty(self):
        "a_dir/empty -> b_dir"
        a_dir = os.path.join(self.test_dir, "a_dir")
        empty = os.path.join(self.test_dir, "a_dir", "empty")
        b_dir = os.path.join(self.test_dir, "b_dir")
        sys.argv = ["pymv", a_dir, b_dir]
        pycp_main()



    def tearDown(self):
        """Remove the temporary directory

        """
        if os.environ.get("DEBUG"):
            print "not removing", self.test_dir
        else:
            shutil.rmtree(self.test_dir)





if os.name == "posix":
    class UnixPrintTransferTestCase(unittest.TestCase):
        def test_01(self):
            src  = "/path/to/foo"
            dest = "/path/to/bar"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, "/path/to/{foo => bar}")

        def test_02(self):
            src  = "/path/to/foo/a/b"
            dest = "/path/to/spam/a/b"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, "/path/to/{foo => spam}/a/b")

        def test_03(self):
            src  = "/path/to/foo/a/b"
            dest = "/path/to/foo/bar/a/b"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, "/path/to/foo/{ => bar}/a/b")

        def test_no_pfx(self):
            src  = "/path/to/foo/a/b"
            dest = "/other/a/b"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, "{/path/to/foo => /other}/a/b")

        def test_no_sfx(self):
            src  = "/path/to/foo/a"
            dest = "/path/to/foo/b"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, "/path/to/foo/{a => b}")

        def test_no_dir(self):
            src  = "a"
            dest = "b"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, "a => b")


if os.name == "nt":
    class DosPrintTransferTestCase(unittest.TestCase):
        def test_01(self):
            src  = r"c:\path\to\foo"
            dest = r"c:\path\to\bar"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, r"c:\path\to\{foo => bar}")

        def test_02(self):
            src  = r"c:\path\to\foo\a\b"
            dest = r"c:\path\to\spam\a\b"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, r"c:\path\to\{foo => spam}\a\b")

        def test_03(self):
            src  = r"c:\path\to\foo\a\b"
            dest = r"c:\path\to\foo\bar\a\b"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, r"c:\path\to\foo\{ => bar}\a\b")

        def test_other_drive(self):
            src  = r"c:\path\to\foo\a\b"
            dest = r"d:\other\a\b"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, r"{c:\path\to\foo => d:\other}\a\b")

        def test_no_sfx(self):
            src  = r"c:\path\to\foo\a"
            dest = r"c:\path\to\foo\b"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, r"c:\path\to\foo\{a => b}")

        def test_no_dir(self):
            src  = "a"
            dest = "b"
            res  = pprint_transfer(src, dest)
            self.assertEquals(res, "a => b")

if __name__ == "__main__" :
    unittest.main()

