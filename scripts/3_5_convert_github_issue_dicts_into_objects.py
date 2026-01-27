from src.types.bug import Bugs
from src.utils.file_util import FileUtil
from src.utils.path_util import PathUtil
from config import APP_NAME_DESKTOP, APP_NAME_VSCODE, APP_NAME_ZETTLR, APP_OWNER_NAME_GODOT, APP_NAME_GODOT, \
    APP_OWNER_NAME_JABREF, APP_NAME_JABREF

if __name__ == "__main__":
    """
    1. convert all issue_dicts into issues
    2. get the last commit date
    3. split issues into train_issues and test_issues by the last commit date
    """

    # ownername = "Zettlr"
    # reponame = APP_NAME_ZETTLR

    # ownername = APP_OWNER_NAME_GODOT
    # reponame = APP_NAME_GODOT

    ownername = APP_OWNER_NAME_JABREF
    reponame = APP_NAME_JABREF

    input_filename = 'issue_dicts'
    filename = 'issues'

    filepath = PathUtil.get_bugs_filepath(reponame, input_filename)

    issue_dicts = FileUtil.load_json(filepath)
    issues = Bugs.from_github_dicts(issue_dicts, ownername, reponame)


    print(f"all issue_dicts: {len(issue_dicts)}")
    print(f"all issues: {len(issues)}")
    filepath = PathUtil.get_bugs_filepath(reponame, filename)
    FileUtil.dump_pickle(filepath, issues)

