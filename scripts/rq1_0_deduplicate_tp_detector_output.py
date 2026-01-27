import json
from pathlib import Path
from copy import deepcopy

from src.utils.file_util import FileUtil
from config import APP_NAME_FIREFOX, OUTPUT_DIR, DATA_DIR


def generate_tp_dedup_labels(input_file: Path, output_file: Path):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_data = {
        "bug_id": data["bug_id"],
        "ground_truth_bug_ids": data.get("ground_truth_bug_ids", []),
        "test_scenarios": []
    }

    seen_ground_truth_hits = set()

    for scenario in data.get("test_scenarios", []):
        new_scenario = {
            "scenario_no": scenario["scenario_no"],
            "discovered_bugs": [],
            "undiscovered_but_revealed_bugs": []
        }

        for bug in scenario.get("discovered_bugs", []):
            if bug.get("is_true_positive") is True:
                hit_gt = bug.get("hit_ground_truth")

                if hit_gt is not None:
                    if hit_gt in seen_ground_truth_hits:
                        is_dup = True
                    else:
                        is_dup = False
                        seen_ground_truth_hits.add(hit_gt)
                else:
                    is_dup = None

                new_scenario["discovered_bugs"].append({
                    "bug_report": deepcopy(bug["bug_report"]),
                    "is_duplicate": is_dup
                })

        new_data["test_scenarios"].append(new_scenario)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print(f"✅ TP dedup labeling file saved to {output_file}")


if __name__ == "__main__":

    reponame = APP_NAME_FIREFOX
    # reponame = APP_NAME_ZETTLR
    # reponame = APP_NAME_JABREF
    # reponame = APP_NAME_GODOT

    output_folder_name = f"detector_output_tp_dedup"
    output_file_name = f"tp_dedup_labels"

    if reponame == APP_NAME_FIREFOX:
        test_bugs_foldername = "test_bugs"
        test_bugs_filename = "test_bugs"
    else:
        test_bugs_foldername = "test_pulls"
        test_bugs_filename = "selected_test_pulls"

    test_bugs_filepath = Path(DATA_DIR, reponame, f'{test_bugs_foldername}')
    output_filepath = Path(OUTPUT_DIR, reponame)
    detector_output_evaluation_filepath = Path(OUTPUT_DIR, reponame, 'detector_output_evaluation')
    test_bugs = FileUtil.load_pickle(Path(test_bugs_filepath, f'{test_bugs_filename}.json'))
    test_bugs = sorted(test_bugs, key=lambda bug: bug.id, reverse=True)

    for bug in test_bugs[0:]:
        if bug:
            bug_id = bug.id
            if reponame != APP_NAME_FIREFOX:
                bug_id = bug.extract_number_from_github_url()
            bug_id = str(bug_id)
            print(f"{bug} ###########################################################")
            detector_output_evaluation_filepath = Path(output_filepath, "detector_output_evaluation", f"{bug_id}_detector_labels.json")
            tp_dedup_output_filepath = Path(output_filepath, output_folder_name, f"{bug_id}_{output_file_name}.json")
            generate_tp_dedup_labels(detector_output_evaluation_filepath, tp_dedup_output_filepath)
