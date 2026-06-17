"""
organizer.py
Core logic for the Intelligent File Organizer.
Handles file scanning, categorization, sorting, and duplicate detection.
"""

import os
import shutil
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# ── Category → extensions mapping ─────────────────────────────────────────────
FILE_CATEGORIES = {
    "Images":      [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg",
                    ".webp", ".tiff", ".ico", ".heic", ".raw"],
    "Videos":      [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv",
                    ".webm", ".m4v", ".3gp", ".mpeg"],
    "Audio":       [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma",
                    ".m4a", ".opus", ".aiff"],
    "Documents":   [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf",
                    ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".md"],
    "Archives":    [".zip", ".tar", ".gz", ".rar", ".7z", ".bz2",
                    ".xz", ".iso", ".dmg"],
    "Code":        [".py", ".js", ".ts", ".html", ".css", ".java",
                    ".cpp", ".c", ".h", ".go", ".rb", ".php",
                    ".sh", ".bat", ".json", ".xml", ".yaml", ".yml",
                    ".sql", ".rs", ".kt", ".swift"],
    "Executables": [".exe", ".msi", ".apk", ".deb", ".rpm", ".pkg",
                    ".appimage"],
    "Fonts":       [".ttf", ".otf", ".woff", ".woff2", ".eot"],
    "Data":        [".db", ".sqlite", ".sqlite3", ".csv", ".tsv",
                    ".parquet", ".hdf5"],
}


def setup_logging(log_dir: str = None) -> logging.Logger:
    """Configure and return a logger that writes to console and optionally a file."""
    logger = logging.getLogger("FileOrganizer")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler (optional)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(
            log_dir, f"organizer_{datetime.now():%Y%m%d_%H%M%S}.log"
        )
        fh = logging.FileHandler(log_path)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.info(f"Logging to {log_path}")

    return logger


def get_category(extension: str) -> str:
    """Return the category for a given file extension (lowercase)."""
    ext = extension.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Others"


def compute_md5(filepath: str, chunk_size: int = 8192) -> str:
    """Return the MD5 hash of a file (used for duplicate detection)."""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def safe_move(src: str, dest_dir: str, logger: logging.Logger) -> str:
    """
    Move *src* into *dest_dir*, renaming automatically if a name collision
    occurs (appends _1, _2, … before the extension).
    Returns the final destination path.
    """
    os.makedirs(dest_dir, exist_ok=True)
    filename  = os.path.basename(src)
    dest_path = os.path.join(dest_dir, filename)

    if os.path.exists(dest_path):
        stem, ext   = os.path.splitext(filename)
        counter     = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(dest_dir, f"{stem}_{counter}{ext}")
            counter  += 1
        logger.debug(f"Name collision resolved → {os.path.basename(dest_path)}")

    shutil.move(src, dest_path)
    return dest_path


# ── Main organizer class ───────────────────────────────────────────────────────

class FileOrganizer:
    """
    Organizes files in a source directory into categorized sub-folders,
    detects duplicates, and provides a detailed report.
    """

    def __init__(
        self,
        source_dir: str,
        output_dir: str = None,
        handle_duplicates: bool = True,
        dry_run: bool = False,
        log_dir: str = None,
    ):
        self.source_dir        = os.path.abspath(source_dir)
        self.output_dir        = os.path.abspath(output_dir or source_dir)
        self.handle_duplicates = handle_duplicates
        self.dry_run           = dry_run
        self.logger            = setup_logging(log_dir)

        # Stats
        self.stats = {
            "total_scanned":   0,
            "moved":           0,
            "duplicates_found": 0,
            "errors":          0,
            "skipped":         0,
        }
        self.moved_files:     list[dict] = []
        self.duplicate_files: list[dict] = []
        self.errors:          list[dict] = []

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _collect_files(self) -> list[str]:
        """Return a flat list of all file paths inside source_dir (non-recursive)."""
        files = []
        with os.scandir(self.source_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    files.append(entry.path)
        return files

    def _find_duplicates(self, files: list[str]) -> dict[str, list[str]]:
        """
        Group files by MD5 hash; return only groups with more than one member.
        """
        hash_map: dict[str, list[str]] = defaultdict(list)
        for filepath in files:
            try:
                file_hash = compute_md5(filepath)
                hash_map[file_hash].append(filepath)
            except Exception as e:
                self.logger.warning(f"Could not hash {filepath}: {e}")
        return {h: paths for h, paths in hash_map.items() if len(paths) > 1}

    # ── Public API ─────────────────────────────────────────────────────────────

    def organize(self) -> dict:
        """
        Run the full organization pipeline.
        Returns a summary dictionary.
        """
        if not os.path.isdir(self.source_dir):
            raise NotADirectoryError(f"Source directory not found: {self.source_dir}")

        mode = "[DRY RUN] " if self.dry_run else ""
        self.logger.info(f"{mode}Starting organization of: {self.source_dir}")
        self.logger.info(f"Output directory          : {self.output_dir}")

        files = self._collect_files()
        self.stats["total_scanned"] = len(files)
        self.logger.info(f"Found {len(files)} file(s) to process.")

        # ── Duplicate detection ────────────────────────────────────────────────
        duplicates: dict[str, list[str]] = {}
        if self.handle_duplicates and files:
            self.logger.info("Scanning for duplicates …")
            duplicates = self._find_duplicates(files)
            if duplicates:
                self.logger.warning(
                    f"Detected {sum(len(v)-1 for v in duplicates.values())} duplicate(s)."
                )

        # Build a set of paths that are "extra" duplicates (keep first occurrence)
        extra_duplicates: set[str] = set()
        for paths in duplicates.values():
            originals, *extras = paths
            for dup in extras:
                extra_duplicates.add(dup)
                self.duplicate_files.append(
                    {"original": originals, "duplicate": dup}
                )
        self.stats["duplicates_found"] = len(extra_duplicates)

        # ── Move files ─────────────────────────────────────────────────────────
        for filepath in files:
            try:
                if filepath in extra_duplicates:
                    dup_dir = os.path.join(self.output_dir, "Duplicates")
                    if not self.dry_run:
                        dest = safe_move(filepath, dup_dir, self.logger)
                    else:
                        dest = os.path.join(dup_dir, os.path.basename(filepath))
                    self.logger.info(f"DUPLICATE → {dest}")
                    continue

                _, ext     = os.path.splitext(filepath)
                category   = get_category(ext)
                dest_dir   = os.path.join(self.output_dir, category)

                if not self.dry_run:
                    dest = safe_move(filepath, dest_dir, self.logger)
                else:
                    dest = os.path.join(dest_dir, os.path.basename(filepath))

                self.logger.info(f"MOVED [{category}] {os.path.basename(filepath)}")
                self.stats["moved"] += 1
                self.moved_files.append(
                    {"source": filepath, "destination": dest, "category": category}
                )

            except Exception as e:
                self.logger.error(f"Error processing {filepath}: {e}")
                self.stats["errors"] += 1
                self.errors.append({"file": filepath, "error": str(e)})

        self._log_summary()
        return self.get_report()

    def get_report(self) -> dict:
        """Return a structured report dictionary."""
        return {
            "source_directory":  self.source_dir,
            "output_directory":  self.output_dir,
            "dry_run":           self.dry_run,
            "timestamp":         datetime.now().isoformat(),
            "stats":             self.stats,
            "moved_files":       self.moved_files,
            "duplicate_files":   self.duplicate_files,
            "errors":            self.errors,
        }

    def _log_summary(self):
        self.logger.info("─" * 50)
        self.logger.info("ORGANIZATION COMPLETE")
        self.logger.info(f"  Total scanned  : {self.stats['total_scanned']}")
        self.logger.info(f"  Files moved    : {self.stats['moved']}")
        self.logger.info(f"  Duplicates     : {self.stats['duplicates_found']}")
        self.logger.info(f"  Errors         : {self.stats['errors']}")
        self.logger.info("─" * 50)
