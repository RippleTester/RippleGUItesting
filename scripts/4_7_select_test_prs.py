import json
from pathlib import Path

from src.pipelines.generation_tool import GenerationTool
from src.pipelines.selector import Selector
from src.utils.file_util import FileUtil
from src.utils.gpt_util import GPTUtil
from config import APP_OWNER_NAME_ZETTLR, APP_NAME_ZETTLR, DATA_DIR, APP_NAME_FIREFOX
from tqdm import tqdm

if __name__ == "__main__":

    ownername = APP_OWNER_NAME_ZETTLR
    reponame = APP_NAME_ZETTLR

    # ownername = APP_OWNER_NAME_GODOT
    # reponame = APP_NAME_GODOT

    # ownername = APP_OWNER_NAME_JABREF
    # reponame = APP_NAME_JABREF

    with_relevant_scenarios = True

    test_pulls_foldername = 'test_pulls'
    test_pulls_filepath = Path(DATA_DIR, reponame, test_pulls_foldername, f"{test_pulls_foldername}.json")

    test_pulls = FileUtil.load_pickle(test_pulls_filepath)
    selector_outputs = []
    selected_test_pulls = []
    for bug in tqdm(test_pulls[0:], ascii=True):
        file_content_filename = "file_contents"
        scenarios_filename = "ranked_scenarios"
        if reponame == APP_NAME_FIREFOX:
            bug_id = bug.id
            input_filepath = Path(DATA_DIR, reponame, test_pulls_foldername, f"{bug.id}")
        else:
            bug_id = bug.extract_number_from_github_url()
        input_filepath = Path(DATA_DIR, reponame, test_pulls_foldername, f"{bug_id}")
        try:
            if with_relevant_scenarios:
                ranked_scenarios = FileUtil.load_json(Path(input_filepath, f"{scenarios_filename}.json"))
                with_relevant_scenarios = ranked_scenarios
            output = Selector.select_pull_for_testing(bug, with_relevant_scenarios, reponame)
            print(json.dumps(output, indent=2))
            selector_outputs.append(output)
            if bool(output["suitable_for_test"]):
                print(f"{bug.id} true")
                selected_test_pulls.append(bug)
        except Exception as e:
            print(e)
            pass
    FileUtil.dump_json(Path(DATA_DIR, reponame, test_pulls_foldername, "selector_outputs.json"), selector_outputs)
    FileUtil.dump_pickle(Path(DATA_DIR, reponame, test_pulls_foldername, f"selected_test_pulls.json"), selected_test_pulls)



