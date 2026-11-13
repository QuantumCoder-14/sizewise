#!/usr/bin/env python3
import sys, unittest, json, io, tempfile, shutil
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sizewise

class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sizewise-"))
    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
    def write(self, rel, size):
        p = self.tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x" * size)
        return p

class TestScan(Base):
    def test_totals(self):
        self.write("a.bin", 100)
        self.write("sub/b.bin", 250)
        r = sizewise.scan(self.tmp)
        self.assertEqual(r["total"], 350)
        self.assertEqual(r["files"], 2)
        self.assertEqual(r["folders"], 1)

    def test_top_files_sorted(self):
        self.write("small.bin", 10)
        self.write("big.bin", 900)
        r = sizewise.scan(self.tmp)
        self.assertEqual(Path(r["top_files"][0][0]).name, "big.bin")

    def test_dir_rollup(self):
        self.write("videos/a.bin", 400)
        self.write("videos/b.bin", 100)
        self.write("docs/c.bin", 50)
        r = sizewise.scan(self.tmp)
        totals = dict(r["top_dirs"])
        self.assertEqual(totals["videos"], 500)
        self.assertEqual(totals["docs"], 50)

    def test_empty_folder(self):
        r = sizewise.scan(self.tmp)
        self.assertEqual((r["total"], r["files"]), (0, 0))

    def test_symlink_not_followed(self):
        self.write("real.bin", 100)
        link = self.tmp / "link.bin"
        try:
            link.symlink_to(self.tmp / "real.bin")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        r = sizewise.scan(self.tmp)
        self.assertEqual(r["total"], 100)

class TestHuman(unittest.TestCase):
    def test_units(self):
        self.assertEqual(sizewise.human(512), "512 B")
        self.assertEqual(sizewise.human(2048), "2.0 KB")
        self.assertEqual(sizewise.human(5 * 1024**2), "5.0 MB")
        self.assertEqual(sizewise.human(3 * 1024**3), "3.0 GB")

class TestCli(Base):
    def test_json_mode(self):
        self.write("a.bin", 42)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = sizewise.main([str(self.tmp), "--json"])
        self.assertEqual(code, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["total"], 42)

    def test_missing_folder(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = sizewise.main([str(self.tmp / "nope")])
        self.assertEqual(code, 2)

    def test_file_instead_of_folder(self):
        f = self.write("a.bin", 10)
        err = io.StringIO()
        with redirect_stderr(err):
            self.assertEqual(sizewise.main([str(f)]), 2)

    def test_report_runs(self):
        self.write("sub/a.bin", 100)
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(sizewise.main([str(self.tmp)]), 0)
        self.assertIn("100 B", buf.getvalue())

if __name__ == "__main__":
    unittest.main(verbosity=1)
