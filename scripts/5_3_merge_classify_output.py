from pathlib import Path
from src.utils.file_util import FileUtil
from config import APP_NAME_FIREFOX, OUTPUT_DIR, APP_NAME_VSCODE, APP_NAME_GODOT, APP_NAME_JABREF

if __name__ == "__main__":
    """
    Merges all bug files into a single JSON file.
    """
    # Configuration
    # repository_name = APP_NAME_FIREFOX
    # repository_name = APP_NAME_VSCODE
    repository_name = APP_NAME_GODOT
    # repository_name = APP_NAME_JABREF

    foldername = f"classify_output"
    file_format = 'json'

    # Set folder paths
    base_folder = Path(OUTPUT_DIR, repository_name, foldername)

    # Find all files with the specified format
    matching_files = FileUtil.find_files_by_extension(base_folder, file_format)
    print(f"Found {len(matching_files)} matching files to merge.")

    # Merge bug data
    all_bugs = []
    for matching_file in matching_files:
        bugs = FileUtil.load_json(matching_file)
        all_bugs.extend(bugs)
        # print(f"Merged {len(bugs)} bugs from: {file_path}")

    # Log the total count
    print(f"Total bugs merged: {len(all_bugs)}")

    # target_folder = base_folder / folder_name
    merged_file_path = Path(OUTPUT_DIR, repository_name, f"{foldername}.json")

    # Log the paths
    # print(f"Target folder: {target_folder}")
    # print(f"Merged file will be saved to: {merged_file_path}")

    # Save merged data to a single file
    FileUtil.dump_json(merged_file_path, all_bugs)
    print(f"All have been saved to: {merged_file_path}")
