import os
import re


def scan_hpp_files(hpp_root, repo_root, parse_folders):
    hpp_folders = {}
    for folder in parse_folders:
        folder_path = os.path.join(hpp_root, repo_root, folder)
        if not os.path.isdir(folder_path):
            print(f"Warning: {folder_path} is not a valid directory, skipping.")
            continue

        hpp_files = []
        for dirpath, _, filenames in os.walk(folder_path):
            for filename in filenames:
                if filename.endswith(".hpp"):
                    hpp_files.append(filename)
        hpp_folders[folder] = sorted(list(set(hpp_files)))
    return hpp_folders


def normalize_type(type_str):
    result = re.sub(r"\bconst\b|\bvolatile\b", "", type_str)
    result = re.sub(r"\s+", " ", result).strip()
    return result
