import json
from pathlib import Path
from config import APP_NAME_FIREFOX, OUTPUT_DIR


def count_tp_before_after_dedup(tp_dedup_file: Path):
    with open(tp_dedup_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    before = 0
    unique_after = 0
    duplicate = 0

    for scenario in data.get("test_scenarios", []):
        for bug in scenario.get("discovered_bugs", []):
            before += 1
            if bug.get("is_duplicate") is True:
                duplicate += 1
            else:
                # false or null 都算 unique
                unique_after += 1

    return before, unique_after, duplicate


if __name__ == "__main__":
    reponame = APP_NAME_FIREFOX

    tp_dedup_dir = Path(OUTPUT_DIR, reponame, "detector_output_tp_dedup")

    total_before = 0
    total_unique = 0
    total_duplicate = 0

    for file in sorted(tp_dedup_dir.glob("*_tp_dedup_labels.json")):
        before, unique_after, duplicate = count_tp_before_after_dedup(file)
        print(
            f"{file.name}: "
            f"before={before}, unique_after={unique_after}, duplicate={duplicate}"
        )

        total_before += before
        total_unique += unique_after
        total_duplicate += duplicate

    print("\n========== Overall Summary ==========")
    print(f"Total TP bug reports (before dedup): {total_before}")
    print(f"Total unique TP bugs (after dedup): {total_unique}")
    print(f"Total duplicate TP bug reports: {total_duplicate}")
