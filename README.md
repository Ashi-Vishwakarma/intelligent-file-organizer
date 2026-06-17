# 🗂 Intelligent File Organizer

> An automated file management system that sorts files into categorized folders based on their type and extension — with duplicate detection, a CLI, a Tkinter GUI, and SQLite history.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Auto-categorization** | 9 categories — Images, Videos, Audio, Documents, Archives, Code, Executables, Fonts, Data, Others |
| **Duplicate detection** | MD5-based hashing; duplicates moved to a `Duplicates/` folder |
| **Dry-run mode** | Preview all changes without touching any files |
| **CLI interface** | Full-featured command-line tool with flags and JSON report export |
| **GUI (Tkinter)** | Dark-themed desktop app with real-time log output |
| **SQLite history** | Every run saved to a local database for auditing |
| **Safe rename** | Automatic `_1`, `_2` suffix if destination filename already exists |
| **Logging** | Console + optional rotating log files |

---

## 📁 Project Structure

```
intelligent-file-organizer/
├── main.py                  # Entry point (CLI or GUI)
├── requirements.txt
├── README.md
├── src/
│   ├── organizer.py         # Core logic (FileOrganizer class)
│   ├── cli.py               # Argparse CLI
│   ├── gui.py               # Tkinter GUI
│   └── database.py          # SQLite history/report storage
└── tests/
    └── test_organizer.py    # Pytest unit tests
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+  
- No third-party packages required (`tkinter` and `sqlite3` are in the standard library)

```bash
git clone https://github.com/<your-username>/intelligent-file-organizer.git
cd intelligent-file-organizer
pip install -r requirements.txt   # only needed for pytest
```

---

## 🖥 Usage

### CLI

```bash
# Basic — organize Downloads in place
python main.py --source ~/Downloads

# Organize into a separate output folder
python main.py --source ~/Downloads --output ~/Organized

# Preview changes without moving anything
python main.py --source ~/Desktop --dry-run

# Save a JSON report
python main.py --source ~/Downloads --report report.json

# Disable duplicate detection (faster)
python main.py --source ~/Downloads --no-duplicates

# Write logs to a file
python main.py --source ~/Downloads --log-dir ./logs
```

Full option list:

```
--source,  -s   (required) Directory to organize
--output,  -o   Output directory (default: same as source)
--dry-run, -d   Preview only; no files moved
--no-duplicates Skip duplicate detection
--log-dir       Directory for log files
--report,  -r   Save JSON report to this path
```

### GUI

```bash
python main.py --gui
```

1. Click **Browse** to select the source folder  
2. (Optional) Choose a separate output folder  
3. Toggle **Dry Run** to preview, or **Detect Duplicates** to enable MD5 scanning  
4. Click **▶ Organize Files** — live logs appear in the console panel

### As a Python library

```python
from src.organizer import FileOrganizer

organizer = FileOrganizer(
    source_dir        = "/home/user/Downloads",
    output_dir        = "/home/user/Organized",
    handle_duplicates = True,
    dry_run           = False,
)

report = organizer.organize()
print(report["stats"])
# {'total_scanned': 42, 'moved': 39, 'duplicates_found': 2, 'errors': 0, 'skipped': 0}
```

### Saving history to SQLite

```python
from src.organizer import FileOrganizer
from src.database  import OrganizerDB

organizer = FileOrganizer("/home/user/Downloads")
report    = organizer.organize()

db = OrganizerDB()
session_id = db.save_report(report)
print(f"Session saved: {session_id}")
print(db.get_statistics())
```

---

## 📂 File Categories

| Category | Extensions |
|---|---|
| **Images** | `.jpg` `.jpeg` `.png` `.gif` `.bmp` `.svg` `.webp` `.tiff` `.ico` `.heic` `.raw` |
| **Videos** | `.mp4` `.avi` `.mov` `.mkv` `.flv` `.wmv` `.webm` `.m4v` `.3gp` `.mpeg` |
| **Audio** | `.mp3` `.wav` `.flac` `.aac` `.ogg` `.wma` `.m4a` `.opus` `.aiff` |
| **Documents** | `.pdf` `.doc` `.docx` `.txt` `.odt` `.rtf` `.xls` `.xlsx` `.ppt` `.pptx` `.csv` `.md` |
| **Archives** | `.zip` `.tar` `.gz` `.rar` `.7z` `.bz2` `.xz` `.iso` `.dmg` |
| **Code** | `.py` `.js` `.ts` `.html` `.css` `.java` `.cpp` `.go` `.rb` `.php` `.sh` `.sql` … |
| **Executables** | `.exe` `.msi` `.apk` `.deb` `.rpm` `.pkg` |
| **Fonts** | `.ttf` `.otf` `.woff` `.woff2` `.eot` |
| **Data** | `.db` `.sqlite` `.parquet` `.hdf5` |
| **Others** | Everything else |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Expected output:
```
tests/test_organizer.py::TestGetCategory::test_image PASSED
tests/test_organizer.py::TestGetCategory::test_video PASSED
...
========================= 17 passed in 0.42s =========================
```

---

## 🗄 SQLite Schema

```sql
-- sessions: one row per organize() call
CREATE TABLE sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_dir    TEXT,
    output_dir    TEXT,
    dry_run       INTEGER,
    total_scanned INTEGER,
    moved         INTEGER,
    duplicates    INTEGER,
    errors        INTEGER,
    created_at    TEXT
);

-- file_records: one row per file processed
CREATE TABLE file_records (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER REFERENCES sessions(id),
    source_path  TEXT,
    dest_path    TEXT,
    category     TEXT,
    is_duplicate INTEGER,
    created_at   TEXT
);
```

---

## 🛠 Tech Stack

- **Python 3.10+**
- `os` — directory traversal, path operations
- `shutil` — file moving
- `hashlib` — MD5 duplicate detection
- `sqlite3` — run history and reporting
- `tkinter` — cross-platform GUI
- `logging` — structured console + file logging
- `argparse` — CLI argument parsing
- `pytest` — unit testing

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🤝 Contributing

Pull requests are welcome!  
1. Fork the repo  
2. Create a feature branch: `git checkout -b feature/my-feature`  
3. Commit your changes: `git commit -m "Add my feature"`  
4. Push and open a PR

---

*Built as a portfolio project demonstrating Python automation, file system management, and software engineering best practices.*
