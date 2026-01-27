from pathlib import Path
from tqdm import tqdm
from src.pipelines.placeholder import Placeholder
from src.types.bug import Bugs
from src.utils.file_util import FileUtil
from config import APP_NAME_FIREFOX, OUTPUT_DIR, DATA_DIR, APP_NAME_VSCODE, APP_NAME_ZETTLR, APP_NAME_GODOT, \
    APP_NAME_JABREF

if __name__ == "__main__":
    # reponame = APP_NAME_FIREFOX
    # reponame = APP_NAME_VSCODE
    # reponame = APP_NAME_ZETTLR
    reponame = APP_NAME_GODOT
    # reponame = APP_NAME_JABREF

    bugs_filename = f"bugs"
    classify_output_filename = f"classify_output"
    bugs = FileUtil.load_pickle(Path(DATA_DIR, reponame, f"filter_by_creation_time_and_desc_{bugs_filename}.json"))
    classify_output = FileUtil.load_json(Path(OUTPUT_DIR, reponame, f"{classify_output_filename}.json"))

    print(f"all bugs: {len(bugs)}")
    filter_bugs = Bugs()
    bug_id_set = set()
    for index, one_output in tqdm(enumerate(classify_output), ascii=True):
        try:
            if one_output['include_scenario'] == True:
                bug_id_set.add(one_output[Placeholder.BUG_ID])
        except Exception:
            # print(f"{index}: {one_output}")
            pass
    print(len(bug_id_set))
    for bug in tqdm(bugs, ascii=True):
        if bug.id in bug_id_set:
            filter_bugs.append(bug)
    print(f"filter bugs: {len(filter_bugs)}")
    FileUtil.dump_pickle(Path(DATA_DIR, reponame, f"filter_by_creation_time_and_desc_with_scenario_{bugs_filename}.json"), filter_bugs)

    for bug in tqdm(bugs, ascii=True):
        # if bug.id not in bug_id_set:
        if bug.id in bug_id_set:
            print(bug)
            print(bug.description.text)
            print("##############################################################")


