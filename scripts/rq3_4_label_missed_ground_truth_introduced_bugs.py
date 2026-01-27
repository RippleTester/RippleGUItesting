from pathlib import Path
import json
from dataclasses import dataclass, asdict
from collections import defaultdict
from config import APP_NAME_FIREFOX, OUTPUT_DIR, MOZILLA_BUG_LINK


# ===================== Data Class =====================

@dataclass
class MissedBugReasonLabel:
    parent_bug_id: int
    introduced_bug_id: int
    missed_reason: str
    note: str = ""


# ===================== Helpers =====================

def load_reason_pool(reason_pool_path: Path):
    if reason_pool_path.exists():
        return json.loads(reason_pool_path.read_text(encoding="utf-8"))
    return []


def save_reason_pool(reason_pool, reason_pool_path: Path):
    reason_pool_path.parent.mkdir(parents=True, exist_ok=True)
    reason_pool_path.write_text(
        json.dumps(sorted(set(reason_pool)), indent=2),
        encoding="utf-8"
    )


def choose_or_add_reason(reason_pool):
    print("\nSelect a reason for why this bug was missed:")
    for i, r in enumerate(reason_pool, start=1):
        print(f"{i}. {r}")
    print(f"{len(reason_pool) + 1}. Add a new reason")

    choice = input("Your choice (number): ").strip()

    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(reason_pool):
            return reason_pool[idx - 1]
        if idx == len(reason_pool) + 1:
            new_reason = input("Enter new missed reason: ").strip()
            if new_reason:
                reason_pool.append(new_reason)
                return new_reason

    print("Invalid input, please enter a reason manually.")
    return input("Enter missed reason: ").strip()


# ===================== Main Labeling Logic =====================

def label_missed_gui_bugs(
    introduced_bug_labels,
    output_path: Path,
    reason_pool_path: Path
):
    reason_pool = load_reason_pool(reason_pool_path)
    results = []

    # group by test bug
    grouped = defaultdict(list)
    for item in introduced_bug_labels:
        if (
            item["detected_by_us"] is False and
            item["bug_type"] == "GUI bug" and
            item["bug_status"] == "Valid bug"
        ):
            grouped[item["parent_bug_id"]].append(item)

    for parent_bug_id, bugs in grouped.items():
        print("\n" + "=" * 80)
        print(f"Test Bug ID (PR): {MOZILLA_BUG_LINK}{parent_bug_id}")
        print("=" * 80)

        for bug in bugs:
            introduced_bug_id = bug["introduced_bug_id"]

            print("\n" + "-" * 60)
            print(f"Introduced Bug ID: {MOZILLA_BUG_LINK}{introduced_bug_id}")
            print("Please inspect the bug report before labeling.")

            missed_reason = choose_or_add_reason(reason_pool)
            note = input("Optional note (press Enter to skip): ").strip()

            results.append(
                MissedBugReasonLabel(
                    parent_bug_id=parent_bug_id,
                    introduced_bug_id=introduced_bug_id,
                    missed_reason=missed_reason,
                    note=note
                )
            )

    save_reason_pool(reason_pool, reason_pool_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved missed-bug reason labels to {output_path}")


if __name__ == "__main__":

    input_file = Path(
        OUTPUT_DIR, APP_NAME_FIREFOX, "introduced_bug_labels.json"
    )
    output_file = Path(
        OUTPUT_DIR, APP_NAME_FIREFOX, "missed_gui_bug_reasons.json"
    )
    reason_pool_file = Path(
        OUTPUT_DIR, APP_NAME_FIREFOX, "missed_reasons_pool.json"
    )

    introduced_bug_labels = json.loads(
        input_file.read_text(encoding="utf-8")
    )

    label_missed_gui_bugs(
        introduced_bug_labels,
        output_file,
        reason_pool_file
    )
