"""
test_organizer.py
Unit tests for the Intelligent File Organizer.
Run with: pytest tests/ -v
"""

import os
import shutil
import tempfile
import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from organizer import FileOrganizer, get_category, compute_md5


# ── Helper ─────────────────────────────────────────────────────────────────────

def _make_file(directory: str, name: str, content: bytes = b"test") -> str:
    path = os.path.join(directory, name)
    with open(path, "wb") as f:
        f.write(content)
    return path


# ── Category mapping ────────────────────────────────────────────────────────────

class TestGetCategory:
    def test_image(self):        assert get_category(".jpg")  == "Images"
    def test_video(self):        assert get_category(".mp4")  == "Videos"
    def test_audio(self):        assert get_category(".mp3")  == "Audio"
    def test_document(self):     assert get_category(".pdf")  == "Documents"
    def test_archive(self):      assert get_category(".zip")  == "Archives"
    def test_code(self):         assert get_category(".py")   == "Code"
    def test_unknown(self):      assert get_category(".xyz")  == "Others"
    def test_case_insensitive(self): assert get_category(".JPG") == "Images"


# ── MD5 hashing ─────────────────────────────────────────────────────────────────

class TestComputeMd5:
    def test_same_content(self, tmp_path):
        f1 = tmp_path / "a.txt"; f1.write_bytes(b"hello")
        f2 = tmp_path / "b.txt"; f2.write_bytes(b"hello")
        assert compute_md5(str(f1)) == compute_md5(str(f2))

    def test_different_content(self, tmp_path):
        f1 = tmp_path / "a.txt"; f1.write_bytes(b"hello")
        f2 = tmp_path / "b.txt"; f2.write_bytes(b"world")
        assert compute_md5(str(f1)) != compute_md5(str(f2))


# ── FileOrganizer ───────────────────────────────────────────────────────────────

class TestFileOrganizer:

    def setup_method(self):
        self.src = tempfile.mkdtemp()
        self.out = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.src, ignore_errors=True)
        shutil.rmtree(self.out, ignore_errors=True)

    # -- basic organization

    def test_organizes_image(self):
        _make_file(self.src, "photo.jpg")
        org = FileOrganizer(self.src, self.out)
        report = org.organize()
        assert os.path.isfile(os.path.join(self.out, "Images", "photo.jpg"))
        assert report["stats"]["moved"] == 1

    def test_organizes_multiple_categories(self):
        _make_file(self.src, "doc.pdf")
        _make_file(self.src, "song.mp3")
        _make_file(self.src, "script.py")
        org = FileOrganizer(self.src, self.out)
        org.organize()
        assert os.path.isfile(os.path.join(self.out, "Documents", "doc.pdf"))
        assert os.path.isfile(os.path.join(self.out, "Audio",     "song.mp3"))
        assert os.path.isfile(os.path.join(self.out, "Code",      "script.py"))

    def test_unknown_extension_goes_to_others(self):
        _make_file(self.src, "mystery.xyz123")
        org = FileOrganizer(self.src, self.out)
        org.organize()
        assert os.path.isfile(os.path.join(self.out, "Others", "mystery.xyz123"))

    # -- duplicate handling

    def test_duplicate_moved_to_duplicates_folder(self):
        content = b"identical content"
        _make_file(self.src, "a.jpg", content)
        _make_file(self.src, "b.jpg", content)
        org = FileOrganizer(self.src, self.out, handle_duplicates=True)
        report = org.organize()
        assert report["stats"]["duplicates_found"] == 1
        dup_dir = os.path.join(self.out, "Duplicates")
        assert os.path.isdir(dup_dir)

    def test_no_duplicate_handling_when_disabled(self):
        content = b"same"
        _make_file(self.src, "a.txt", content)
        _make_file(self.src, "b.txt", content)
        org = FileOrganizer(self.src, self.out, handle_duplicates=False)
        report = org.organize()
        assert report["stats"]["duplicates_found"] == 0

    # -- dry run

    def test_dry_run_does_not_move_files(self):
        _make_file(self.src, "image.png")
        org = FileOrganizer(self.src, self.out, dry_run=True)
        org.organize()
        # File should still be in source
        assert os.path.isfile(os.path.join(self.src, "image.png"))
        # Nothing in output
        assert not os.path.isfile(os.path.join(self.out, "Images", "image.png"))

    # -- edge cases

    def test_empty_directory(self):
        org = FileOrganizer(self.src, self.out)
        report = org.organize()
        assert report["stats"]["total_scanned"] == 0
        assert report["stats"]["moved"] == 0

    def test_invalid_source_raises(self):
        with pytest.raises(NotADirectoryError):
            FileOrganizer("/nonexistent/path", self.out).organize()

    def test_report_structure(self):
        _make_file(self.src, "test.txt")
        report = FileOrganizer(self.src, self.out).organize()
        for key in ("source_directory", "output_directory", "dry_run",
                    "timestamp", "stats", "moved_files",
                    "duplicate_files", "errors"):
            assert key in report
