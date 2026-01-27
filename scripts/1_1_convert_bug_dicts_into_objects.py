from pathlib import Path

from tqdm import tqdm

from src.types.bug import Bugs, Bug
from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_FIREFOX

if __name__ == "__main__":
    """
    1. convert all bug_dicts into bugs
    """
    reponame = APP_NAME_FIREFOX
    save_foldername = Path(DATA_DIR, reponame, "test_bugs")

    bug_dicts = FileUtil.load_json(Path(save_foldername, f"test_bug_dicts.json"))

    bugs = []
    count = 0
    for bug_dict in tqdm(bug_dicts, ascii=True):
        bug = Bug.from_dict(bug_dict)
        print(bug)
        bugs.append(bug)
    bugs = Bugs(bugs)
    bugs.overall()
    print(f"all bugs: {len(bug_dicts)}")
    print(f"all bugs: {len(bugs)}")

    print(save_foldername)
    FileUtil.dump_pickle(Path(save_foldername, f"test_bugs.json"), bugs)

