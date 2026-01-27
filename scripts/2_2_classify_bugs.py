import os
from datetime import datetime
from pathlib import Path

from src.pipelines.constructor import ScenarioExtractor
from src.types.product_component_pair import ProductComponentPair
from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_FIREFOX, OUTPUT_DIR
from tqdm import tqdm


if __name__ == "__main__":

    reponame = APP_NAME_FIREFOX
    bug_objects = "bugs"
    start_index = 0
    end_index = 490644
    bugs_filename = f'{bug_objects}_{start_index}_{end_index}.json'
    filter_bugs_filename = f'filter_by_creation_time_and_desc_{bugs_filename}'
    filepath = Path(DATA_DIR, reponame, filter_bugs_filename)
    bugs = FileUtil.load_pickle(filepath)
    bugs.overall()

    product_component_pair_list = set()
    for bug in tqdm(bugs):
        product_component_pair_list.add(bug.product_component_pair)
    product_component_pair_list = list(product_component_pair_list)
    print(f"{len(product_component_pair_list)}")

    pc_bugs_dict = bugs.classify_bugs_by_product_component_pair_list(product_component_pair_list)

    for pc_index, pc in enumerate(product_component_pair_list):
        pc_bugs = pc_bugs_dict[pc]
        print(f"{pc_index}: {pc} - {len(pc_bugs)}")
        output_filepath = Path(OUTPUT_DIR, reponame, f"{pc.product}::{pc.component}")
        if not os.path.exists(output_filepath):
            # If it doesn't exist, create itv
            os.makedirs(output_filepath)
        output_list = []
        for bug_index, pc_bug in enumerate(tqdm(pc_bugs, ascii=True)):
            try:
                output = ScenarioExtractor.extract_scenarios(pc_bug)
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

