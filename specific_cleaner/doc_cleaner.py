#!/usr/bin/env python3

import os
import sys
from pathlib import Path


DOC_EXTENSIONS = [
    ".doc",
    ".docx",
    ".md",
    ".ini",
    ".lnk",
    ".sav",
    ".dll",
    ".gif",
    ".thm",
    ".lrv",
    ".poh",
]


def clean_doc_files(path: str) -> None:
    target_path = Path(path)

    if not target_path.exists():
        print(f"Error: Path '{path}' does not exist")
        return

    if not target_path.is_dir():
        print(f"Error: '{path}' is not a directory")
        return

    removed_count = 0

    for file_path in target_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in DOC_EXTENSIONS:
            try:
                file_path.unlink()
                print(f"Removed: {file_path}")
                removed_count += 1
            except OSError as e:
                print(f"Error removing {file_path}: {e}")

    print(f"\nCleaning complete. Removed {removed_count} document files.")


def main():
    if len(sys.argv) != 2:
        print("Usage: python doc_cleaner.py <path>")
        sys.exit(1)

    path = sys.argv[1]
    clean_doc_files(path)


if __name__ == "__main__":
    main()
