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
    bug_ids = sorted(
        int(p.name)
        for p in test_bugs_path.iterdir()
        if p.is_dir() and p.name.isdigit()
    )

    print(bug_ids)
    print(len(bug_ids))

    for bug_id in bug_ids:
        test_bug = test_bugs.get_bug_by_id(bug_id)
        pulls.append(test_bug)
    print(len(pulls))
    for pull in pulls:
        print(pull)

    FileUtil.dump_pickle(Path(test_bugs_path, "test_bugs.json"), pulls)
