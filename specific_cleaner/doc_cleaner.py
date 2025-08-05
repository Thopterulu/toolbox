#!/usr/bin/env python3

import os
import sys
import re
from pathlib import Path
import fnmatch


DOC_EXTENSIONS = [
    ".adx",
    ".axd",
    ".csv",
    ".conf*",
    ".dat",
    # ".doc",
    # ".docx",
    ".md",
    ".ini",
    ".lnk",
    ".sav",
    ".dll",
    ".gif",
    ".ico",
    ".js",
    ".json*",
    ".lnk",
    ".log",
    ".thm",
    ".lrv",
    ".md",
    ".msc",
    ".poh",
    ".sav",
    ".thm",
    ".wks",
    ".csv",
    ".xlsm",
    ".xls",
    ".adx",
    ".axd",
    ".dat",
    ".json",
    ".xml",
    ".log",
    ".wks",
    ".ico",
    ".dat",
    ".js",
    ".msg",
    ".téléchargement",
    ".php",
    ".bat",
    ".ps",
    ".xmind",
    ".sqlite*",
    ".metadata",
    ".lua",
    ".msi",
    ".exe",
    ".tmp",
    ".err",
    ".bin",
    ".dbf",
]

PROGRAMMING_EXTENSIONS = [
    ".lua",
    ".js",
    ".ts",
    ".py",
    ".go",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".rs",
    ".scala",
    ".sh",
    ".ps1",
    ".r",
    ".m",
    ".pl",
    ".sql",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".vue",
    ".jsx",
    ".tsx",
    ".dart",
    ".elm",
    ".clj",
    ".ex",
    ".exs",
    ".hs",
    ".ml",
    ".fs",
    ".vb",
    ".pas",
    ".asm",
    ".s",
]


def matches_extension(file_extension: str, extension_patterns: list[str]) -> bool:
    """Check if file extension matches any pattern in the list, supporting wildcards."""
    for pattern in extension_patterns:
        if "*" in pattern:
            if fnmatch.fnmatch(file_extension, pattern):
                return True
        else:
            if file_extension == pattern:
                return True
    return False


def contains_uuid_pattern(filename: str) -> bool:
    """Check if filename contains a UUID pattern like 0785B20-3CDD-41CD-9B21-82D45AB240B2."""
    uuid_pattern = (
        r"[0-9A-Fa-f]{7,8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"
    )
    return bool(re.search(uuid_pattern, filename))


def should_remove_uuid_file(file_path: Path) -> bool:
    """Check if UUID file should be removed (always true for UUID pattern files)."""
    return True


def clean_doc_files(path: str) -> None:
    target_path = Path(path)

    if not target_path.exists():
        print(f"Error: Path '{path}' does not exist")
        return

    if not target_path.is_dir():
        print(f"Error: '{path}' is not a directory")
        return

    removed_count = 0

    all_extensions = DOC_EXTENSIONS + PROGRAMMING_EXTENSIONS

    for file_path in target_path.rglob("*"):
        should_remove = False
        removal_reason = ""

        if file_path.is_file():
            # Check if file has matching extension
            if matches_extension(file_path.suffix.lower(), all_extensions):
                should_remove = True
                removal_reason = f"extension {file_path.suffix.lower()}"
            # Check if file has UUID pattern and remove it
            elif contains_uuid_pattern(file_path.name):
                should_remove = should_remove_uuid_file(file_path)
                if should_remove:
                    removal_reason = "UUID pattern file"

        if should_remove:
            try:
                file_path.unlink()
                print(f"Removed: {file_path} ({removal_reason})")
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
