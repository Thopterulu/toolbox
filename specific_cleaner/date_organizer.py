#!/usr/bin/env python3

import sys
import shutil
from pathlib import Path
from datetime import datetime

DATE_FOLDER_FORMAT = "%Y-%m"


def organize_files_by_date(path: str) -> None:
    target_path = Path(path)

    if not target_path.exists():
        print(f"Error: Path '{path}' does not exist")
        return

    if not target_path.is_dir():
        print(f"Error: '{path}' is not a directory")
        return

    moved_count = 0
    error_count = 0

    # Get all existing date directories to avoid moving them
    existing_date_dirs = set()
    for item in target_path.iterdir():
        if item.is_dir() and len(item.name) == 10 and item.name.count("-") == 2:
            try:
                datetime.strptime(item.name, DATE_FOLDER_FORMAT)
                existing_date_dirs.add(item.name)
            except ValueError:
                pass

    # Process all files recursively
    for file_path in target_path.rglob("*"):
        if file_path.is_file():
            # Skip files that are already in date directories at root level
            relative_parts = file_path.relative_to(target_path).parts
            if len(relative_parts) > 1 and relative_parts[0] in existing_date_dirs:
                continue

            # Skip files in $RECYCLE.BIN directories
            if len(relative_parts) > 1 and relative_parts[0] == "$RECYCLE.BIN":
                continue

            try:
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                date_folder = mod_time.strftime(DATE_FOLDER_FORMAT)

                dest_dir = target_path / date_folder
                dest_dir.mkdir(exist_ok=True)

                dest_file = dest_dir / file_path.name

                if dest_file.exists():
                    base_name = file_path.stem
                    suffix = file_path.suffix
                    counter = 1
                    while dest_file.exists():
                        dest_file = dest_dir / f"{base_name}_{counter}{suffix}"
                        counter += 1

                shutil.move(str(file_path), str(dest_file))
                relative_path = file_path.relative_to(target_path)
                print(f"Moved: {relative_path} -> {date_folder}/")
                moved_count += 1

            except OSError as e:
                relative_path = file_path.relative_to(target_path)
                print(f"Error moving {relative_path}: {e}")
                error_count += 1

    print("\nOrganization complete.")
    print(f"Files moved: {moved_count}")
    if error_count > 0:
        print(f"Errors: {error_count}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python date_organizer.py <path>")
        sys.exit(1)

    path = sys.argv[1]
    organize_files_by_date(path)


if __name__ == "__main__":
    main()
