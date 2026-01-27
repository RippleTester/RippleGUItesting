import json
from pathlib import Path

from src.pipelines.generation_tool import GenerationTool
from src.pipelines.placeholder import Placeholder
from src.pipelines.selector import Selector
from src.types.bug import Bugs
from src.utils.file_util import FileUtil
from src.utils.gpt_util import GPTUtil
from config import APP_OWNER_NAME_ZETTLR, APP_NAME_ZETTLR, DATA_DIR, APP_NAME_FIREFOX, APP_NAME_JABREF, \
    APP_OWNER_NAME_JABREF, APP_OWNER_NAME_GODOT, APP_NAME_GODOT
from tqdm import tqdm

if __name__ == "__main__":

    # ownername = APP_OWNER_NAME_ZETTLR
    # reponame = APP_NAME_ZETTLR

    ownername = APP_OWNER_NAME_GODOT
    reponame = APP_NAME_GODOT

    # ownername = APP_OWNER_NAME_JABREF
    # reponame = APP_NAME_JABREF

    with_relevant_scenarios = True

    test_pulls_foldername = 'test_pulls'
    test_pulls_filepath = Path(DATA_DIR, reponame, test_pulls_foldername, f"{test_pulls_foldername}.json")

    test_pulls = FileUtil.load_pickle(test_pulls_filepath)
    test_pulls = Bugs(test_pulls)
    selector_outputs = FileUtil.load_json(Path(DATA_DIR, reponame, test_pulls_foldername, "selector_outputs.json"))

    selected_test_pulls = []
    for selector_output in tqdm(selector_outputs[0:49], ascii=True):
        if selector_output['suitable_for_test']:
            bug_id = str(selector_output[Placeholder.BUG_ID])
            bug = test_pulls.get_bug_by_id(bug_id)
            selected_test_pulls.append(bug)
            print(bug)
    print(len(selected_test_pulls))
    FileUtil.dump_pickle(Path(DATA_DIR, reponame, test_pulls_foldername, f"selected_test_pulls.json"), selected_test_pulls)



