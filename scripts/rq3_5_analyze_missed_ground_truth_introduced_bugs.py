import json
from collections import Counter, defaultdict
from pathlib import Path

from config import OUTPUT_DIR, APP_NAME_FIREFOX


def analyze_missed_bug_reasons(json_path: Path):
    data = json.loads(json_path.read_text(encoding="utf-8"))

    # =====================
    # 1. missed_reason frequency
    # =====================
    reason_counter = Counter()
    for item in data:
        reason = item["missed_reason"].strip()
        reason_counter[reason] += 1

    print("\n=== Missed Bug Reasons (Frequency) ===")
    for reason, cnt in reason_counter.most_common():
        print(f"{cnt:>3}  |  {reason}")

    # =====================
    # 2. by PR(parent bug) to calculate miss number
    # =====================
    pr_counter = Counter()
    for item in data:
        pr_counter[item["parent_bug_id"]] += 1

    print("\n=== Missed Bugs per PR ===")
    for pr, cnt in pr_counter.most_common():
        print(f"PR {pr}: {cnt} missed bugs")

    return reason_counter, pr_counter


if __name__ == "__main__":
    reponame = APP_NAME_FIREFOX
    input_file = Path(OUTPUT_DIR, reponame, "missed_gui_bug_reasons.json")

    analyze_missed_bug_reasons(input_file)
