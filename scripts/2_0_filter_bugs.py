from datetime import datetime
from pathlib import Path

from src.types.bug import Bugs
from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_FIREFOX, APP_NAME_THUNDERBIRD
from tqdm import tqdm


if __name__ == "__main__":

    """
    1. creation time >= datetime(2019, 5, 1, 0, 0, 0)
    2. desc not None and not log
    """

    reponame = APP_NAME_FIREFOX
    bug_dicts = "bug_dicts"
    bug_objects = "bugs"
    start_index = 0
    # end_index = 72621
    end_index = 490644
    bug_dicts_filename = f'{bug_dicts}_{start_index}_{end_index}.json'
    bugs_filename = f'{bug_objects}_{start_index}_{end_index}.json'
    filepath = Path(DATA_DIR, reponame, bug_dicts_filename)

    bug_dicts = FileUtil.load_json(filepath)
    bugs = Bugs.from_dicts(bug_dicts)
    bugs.sort_by_creation_time(reverse=True)
    print(f"all_bugs_len: {len(bugs)}\n"
          f"Start creation_time: {bugs[0].creation_time}\n"
          f"End creation_time: {bugs[-1].creation_time}")
    FileUtil.dump_pickle(Path(DATA_DIR, reponame, f"{bugs_filename}"), bugs)

    filter_bugs = Bugs()
    cutoff = datetime(2019, 5, 1, 0, 0, 0)

    for index, bug in tqdm(enumerate(bugs)):
        if bug.creation_time >= cutoff:
            filter_bugs.append(bug)
    bugs = filter_bugs
    FileUtil.dump_pickle(Path(DATA_DIR, reponame, f"filter_by_creation_time_{bugs_filename}"), bugs)
    # bugs = FileUtil.load_pickle(Path(DATA_DIR, reponame, f"filter_by_creation_time_{bugs_filename}"))
    print("###################################################################")
    print(f"filter_bugs_by_creation_time_len: {len(bugs)}\n"
          f"cutoff creation_time: {cutoff}\n"
          f"Start creation_time: {bugs[0].creation_time}\n"
          f"End creation_time: {bugs[-1].creation_time}")

    filter_bugs = Bugs()
    for bug in tqdm(bugs):
        if not bug.is_log_bug() and bug.description.text.strip():
            filter_bugs.append(bug)
    bugs = filter_bugs
    print("###################################################################")
    print(f"filter_bugs_by_log_desc_len: {len(bugs)}\n"
          f"Start creation_time: {bugs[0].creation_time}\n"
          f"End creation_time: {bugs[-1].creation_time}")

    FileUtil.dump_pickle(Path(DATA_DIR, reponame, f"filter_by_creation_time_and_desc_{bugs_filename}"), bugs)

