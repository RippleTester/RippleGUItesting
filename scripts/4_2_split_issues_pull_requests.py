from pathlib import Path

from src.types.bug import Bugs
from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_DESKTOP, APP_NAME_VSCODE, APP_NAME_ZETTLR, APP_NAME_GODOT, APP_OWNER_NAME_GODOT, \
    APP_OWNER_NAME_JABREF, APP_NAME_JABREF, APP_OWNER_NAME_ZETTLR

if __name__ == "__main__":
    github = "github"

    # ownername = APP_OWNER_NAME_ZETTLR
    # reponame = APP_NAME_ZETTLR

    # ownername = APP_OWNER_NAME_GODOT
    # reponame = APP_NAME_GODOT

    ownername = APP_OWNER_NAME_JABREF
    reponame = APP_NAME_JABREF

    foldername = "test_issues_pulls"
    filepath = Path(DATA_DIR, reponame)
    issues_pull_requests = FileUtil.load_json(Path(filepath, f"{foldername}.json"))
    print(len(issues_pull_requests))

    issues = []
    pulls = []
    for one in issues_pull_requests:
        if "pull_request" in one.keys():
            pulls.append(one)
        else:
            issues.append(one)

    print(f"all issues: {len(issues)}")
    print(f"all pulls: {len(pulls)}")
    issues = Bugs.filter_bug_dicts_by_github_repo_fullname(issues, f'{ownername}/{reponame}')
    pulls = Bugs.filter_bug_dicts_by_github_repo_fullname(pulls, f'{ownername}/{reponame}')
    print(f"filtered issues by github_repo_fullname: {len(issues)}")
    print(f"filtered pulls by github_repo_fullname: {len(pulls)}")
    FileUtil.dump_json(Path(filepath, f"test_issue_dicts.json"), issues)
    FileUtil.dump_json(Path(filepath, f"test_pull_dicts.json"), pulls)
