#!/usr/bin/env python3

import sys
from pathlib import Path
from collections import Counter


def analyze_extensions(path: str) -> None:
    target_path = Path(path)

    if not target_path.exists():
        print(f"Error: Path '{path}' does not exist")
        return

    if not target_path.is_dir():
        print(f"Error: '{path}' is not a directory")
        return

    extensions = []

    for file_path in target_path.rglob("*"):
        if file_path.is_file():
            ext = file_path.suffix.lower()
            if ext:
                extensions.append(ext)
            else:
                extensions.append("(no extension)")

    if not extensions:
        print("No files found in the directory")
        return

    extension_counts = Counter(extensions)

    print(f"File extension analysis for: {path}")
    print(f"Total files analyzed: {len(extensions)}")
    print(f"Unique extensions found: {len(extension_counts)}")
    print("\nExtensions (sorted by frequency):")
    print("-" * 40)

    for ext, count in extension_counts.most_common():
        percentage = (count / len(extensions)) * 100
        print(f"{ext:<20} {count:>6} files ({percentage:>5.1f}%)")


def main():
    if len(sys.argv) != 2:
        print("Usage: python extension_analyzer.py <path>")
        sys.exit(1)

    path = sys.argv[1]
    analyze_extensions(path)


if __name__ == "__main__":
    main()
