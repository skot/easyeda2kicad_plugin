from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
ARCHIVE = DIST / "easyeda2kicad_plugin.zip"

INCLUDE = [
    ROOT / "LCSC Importer.py",
    ROOT / "README.md",
    ROOT / "easyeda2kicad",
    ROOT / "vendor",
]

SKIP_DIRS = {"__pycache__", ".git", "dist"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".log"}
SKIP_NAMES = {".DS_Store"}


def iter_files(path: Path):
    if path.is_file():
        yield path
        return

    for child in path.rglob("*"):
        if any(part in SKIP_DIRS for part in child.parts):
            continue
        if child.name in SKIP_NAMES:
            continue
        if child.is_file() and child.suffix not in SKIP_SUFFIXES:
            yield child


def main():
    DIST.mkdir(exist_ok=True)
    if ARCHIVE.exists():
        ARCHIVE.unlink()

    with ZipFile(ARCHIVE, "w", ZIP_DEFLATED) as archive:
        for item in INCLUDE:
            for file_path in iter_files(item):
                archive.write(file_path, file_path.relative_to(ROOT))

    print(f"Created {ARCHIVE}")


if __name__ == "__main__":
    main()
