from pathlib import Path

from src.utils.file_util import FileUtil
from config import APP_OWNER_NAME_ZETTLR, APP_NAME_ZETTLR, DATA_DIR, APP_OWNER_NAME_JABREF, APP_NAME_JABREF, \
    APP_NAME_FIREFOX


if __name__ == "__main__":

    reponame = APP_NAME_FIREFOX

    test_bugs_foldername = "test_bugs"

    pulls = []

    test_bugs_path = Path(DATA_DIR, APP_NAME_FIREFOX, test_bugs_foldername)
    test_bugs = FileUtil.load_pickle(Path(test_bugs_path, f"{test_bugs_foldername}.json"))
    introduced_bugs = []
    for bug in test_bugs:
        if bug.relation.regressions:
            # print(bug.relation.regressions)
            introduced_bugs.extend(bug.relation.regressions)
    print(len(introduced_bugs))
    print(len(set(introduced_bugs)))