from pathlib import Path

from tqdm import tqdm

from src.types.bug import Bugs, Bug
from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_FIREFOX, APP_NAME_THUNDERBIRD

if __name__ == "__main__":
    """
    1. convert all bug_dicts into bugs
    """
    reponame = APP_NAME_FIREFOX
    component = None
    start_index = 0
    end_index = -1
    test_flag = False
    bugs_foldername = f"bugs"
    if test_flag:
        bugs_foldername = f"test_{bugs_foldername}"
    save_foldername = Path(DATA_DIR, reponame)

    bug_dicts_foldername = f'bug_dicts_{start_index}_{end_index}'

    if component:
        save_foldername = Path(save_foldername, f'{component}')

    bug_dicts = FileUtil.load_json(Path(save_foldername, "bug_dicts", f"{bug_dicts_foldername}.json"))
    bugs = []
    count = 0
    for bug_dict in tqdm(bug_dicts, ascii=True):
        bug = Bug.from_dict(bug_dict)
        # print(bug)
        bugs.append(bug)
    bugs = Bugs(bugs)
    bugs.overall()
    print(f"all bugs: {len(bug_dicts)}")
    print(f"all bugs: {len(bugs)}")

    print(save_foldername)
    FileUtil.dump_pickle(Path(save_foldername, f"{bugs_foldername}.json"), bugs)
