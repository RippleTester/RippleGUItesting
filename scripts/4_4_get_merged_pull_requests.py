from pathlib import Path
from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_DESKTOP, APP_NAME_VSCODE, APP_NAME_ZETTLR, APP_OWNER_NAME_GODOT, APP_NAME_GODOT, \
    APP_OWNER_NAME_JABREF, APP_NAME_JABREF, APP_OWNER_NAME_ZETTLR

if __name__ == "__main__":
    github = "github"

    # ownername = APP_OWNER_NAME_ZETTLR
    # reponame = APP_NAME_ZETTLR

    # ownername = APP_OWNER_NAME_GODOT
    # reponame = APP_NAME_GODOT

    ownername = APP_OWNER_NAME_JABREF
    reponame = APP_NAME_JABREF

    filepath = Path(DATA_DIR, reponame)
    pulls = FileUtil.load_pickle(Path(filepath, f"test_pulls.json"))
    print(f"all pulls: {len(pulls)}")

    merged_pulls = []
    for one in pulls:
        if one.merged_at:
            merged_pulls.append(one)

    print(f"merged pulls: {len(merged_pulls)}")

    for one in merged_pulls:
        print(one.id)

    FileUtil.dump_pickle(Path(filepath, f"test_merged_pulls.json"), merged_pulls)
