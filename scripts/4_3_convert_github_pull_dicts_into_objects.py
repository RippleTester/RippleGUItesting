from src.types.bug import Bugs
from src.utils.file_util import FileUtil
from src.utils.path_util import PathUtil
from config import APP_NAME_DESKTOP, APP_NAME_VSCODE, APP_NAME_ZETTLR, APP_OWNER_NAME_GODOT, APP_NAME_GODOT, \
    APP_OWNER_NAME_JABREF, APP_NAME_JABREF, APP_OWNER_NAME_ZETTLR

if __name__ == "__main__":

    # ownername = APP_OWNER_NAME_ZETTLR
    # reponame = APP_NAME_ZETTLR

    # ownername = APP_OWNER_NAME_GODOT
    # reponame = APP_NAME_GODOT

    ownername = APP_OWNER_NAME_JABREF
    reponame = APP_NAME_JABREF

    input_filename = "test_pull_dicts"
    filename = 'test_pulls'

    filepath = PathUtil.get_bugs_filepath(reponame, input_filename)

    pull_dicts = FileUtil.load_json(filepath)
    pulls = Bugs.from_github_dicts(pull_dicts, ownername, reponame)

    print(f"all pull_dicts: {len(pull_dicts)}")
    print(f"all pulls: {len(pulls)}")
    # filepath = PathUtil.get_bugs_filepath(reponame, filename)
    # FileUtil.dump_pickle(filepath, pulls)
    FileUtil.dump_pickle(PathUtil.get_bugs_filepath(reponame, f"{filename}"), pulls)


