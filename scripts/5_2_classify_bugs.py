import os
from datetime import datetime
from pathlib import Path

from src.pipelines.constructor import ScenarioExtractor
from src.types.product_component_pair import ProductComponentPair
from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_FIREFOX, OUTPUT_DIR, APP_NAME_VSCODE, APP_NAME_ZETTLR, APP_NAME_GODOT, \
    APP_NAME_JABREF
from tqdm import tqdm


if __name__ == "__main__":

    # reponame = APP_NAME_FIREFOX
    # reponame = APP_NAME_ZETTLR
    reponame = APP_NAME_GODOT
    # reponame = APP_NAME_JABREF
    bug_objects = "bugs"
    # start_index = 0
    # end_index = 490644
    bugs_filename = f'{bug_objects}.json'
    filter_bugs_filename = f'filter_by_creation_time_and_desc_{bugs_filename}'
    filepath = Path(DATA_DIR, reponame, filter_bugs_filename)
    bugs = FileUtil.load_pickle(filepath)

    output_filepath = Path(OUTPUT_DIR, reponame, f"classify_output")
    if not os.path.exists(output_filepath):
        # If it doesn't exist, create itv
        os.makedirs(output_filepath)
    output_list = []
    for bug_index, bug in enumerate(tqdm(bugs, ascii=True)):
        try:
            output = ScenarioExtractor.extract_scenarios(bug)
            output_list.append(output)
        except Exception as e:
            print(f"{e}")
            # print(output)
            pass
        # print("************************************************")
        if bug_index % 100 == 0:
            current_datetime = datetime.now()
            FileUtil.dump_json(Path(output_filepath, f"scenarios_{current_datetime}.json"),
                               output_list)
            output_list = []

    if output_list:
        current_datetime = datetime.now()
        FileUtil.dump_json(Path(output_filepath, f"scenarios_{current_datetime}.json"),
                           output_list)

