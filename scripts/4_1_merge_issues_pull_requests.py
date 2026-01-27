from pathlib import Path
from tqdm import tqdm
from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_VSCODE, APP_NAME_ZETTLR, APP_NAME_GODOT, APP_NAME_JABREF

if __name__ == "__main__":
    github = "github"
    # reponame = APP_NAME_ZETTLR
    # reponame = APP_NAME_GODOT
    reponame = APP_NAME_JABREF
    foldername = "test_issues_pulls"
    filepath = Path(DATA_DIR, reponame)
    filenames = FileUtil.get_file_names_in_directory(Path(filepath, foldername), 'json')
    filenames = sorted(filenames, key=lambda x: (len(x), x))
    issues_pull_requests = []
    for filename in tqdm(filenames, ascii=True):
        temp_issues_pull_requests = FileUtil.load_json(filename)
        issues_pull_requests.extend(temp_issues_pull_requests)
    print(len(issues_pull_requests))
    FileUtil.dump_json(Path(filepath, f"{foldername}.json"), issues_pull_requests)
