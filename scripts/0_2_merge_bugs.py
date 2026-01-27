from pathlib import Path
from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_FIREFOX, APP_NAME_THUNDERBIRD

if __name__ == "__main__":
    """
    Merges all bug files into a single JSON file.
    """
    # Configuration
    repository_name = APP_NAME_FIREFOX
    test_flag = False
    start_index = 0
    end_index = -1
    foldername = f"bugs_{start_index}_{end_index}"
    file_format = 'json'
    bug_dicts_foldername = "bug_dicts"

    # Set folder paths
    base_folder = Path(DATA_DIR, repository_name, bug_dicts_foldername, foldername)

    # Find all files with the specified format
    matching_files = FileUtil.find_files_by_extension(base_folder, file_format)
    print(f"Found {len(matching_files)} matching files to merge.")

    # Merge bug data
    all_bugs = []
    for matching_file in matching_files:
        bugs = FileUtil.load_json(matching_file)
        all_bugs.extend(bugs)

    # Log the total count
    print(f"Total bugs merged: {len(all_bugs)}")

    if end_index is None:
        end_index = len(all_bugs)
    folder_name = f'bugs_{start_index}_{end_index}'

    if test_flag:
        folder_name = f"test_{folder_name}"

    # target_folder = base_folder / folder_name
    merged_file_path = base_folder / f"{folder_name}.json"

    # Log the paths
    print(f"Merged file will be saved to: {merged_file_path}")

    # Save merged data to a single file
    FileUtil.dump_json(merged_file_path, all_bugs)
    print(f"All bugs have been saved to: {merged_file_path}")
