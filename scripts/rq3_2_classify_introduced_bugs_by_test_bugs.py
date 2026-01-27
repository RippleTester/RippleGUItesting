from pathlib import Path
import json
from enum import Enum
from dataclasses import dataclass, asdict

from src.utils.file_util import FileUtil
from config import APP_NAME_FIREFOX, DATA_DIR, OUTPUT_DIR


# ===================== Enums =====================

class IntroducedBugType(Enum):
    LOG = "Crash / stack trace / error log"
    GUI = "GUI bug"
    NON_GUI = "Non-GUI bug or not detectable via GUI"
    OTHER = "Other"


class BugStatus(Enum):
    VALID = "Valid bug"
    DUPLICATE = "Invalid: Duplicate"
    WONTFIX = "Invalid: WontFix"
    WORKSFORME = "Invalid: WorksForMe"
    INVALID = "Invalid: Other"


# ===================== Data Class =====================

@dataclass
class IntroducedBugLabel:
    parent_bug_id: int
    introduced_bug_id: int
    bug_type: str
    bug_status: str
    detected_by_us: bool
    note: str = ""


# ===================== Interactive Helpers =====================

def choose_introduced_bug_type():
    print("\nSelect introduced bug type:")
    for i, e in enumerate(IntroducedBugType, start=1):
        print(f"{i}. {e.value}")
    choice = input("Your choice (number): ").strip()

    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(IntroducedBugType):
            return list(IntroducedBugType)[idx - 1]

    print("Invalid input, defaulting to OTHER.")
    return IntroducedBugType.OTHER


def choose_detected_by_us():
    choice = input("Detected by our approach? (y/n): ").strip().lower()
    if choice in ("y", "yes"):
        return True
    if choice in ("n", "no"):
        return False
    print("Invalid input, defaulting to NO.")
    return False


def choose_bug_status():
    print("\nSelect bug status:")
    for i, e in enumerate(BugStatus, start=1):
        print(f"{i}. {e.value}")
    print(f"{len(BugStatus) + 1}. Other (custom input)")

    choice = input("Your choice (number): ").strip()

    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= len(BugStatus):
            return list(BugStatus)[idx - 1].value
        if idx == len(BugStatus) + 1:
            custom = input("Please specify bug status: ").strip()
            return custom or "Invalid: Unspecified"

    print("Invalid input, defaulting to 'Invalid: Unspecified'")
    return "Invalid: Unspecified"


# ===================== Main Labeling Logic =====================

def label_introduced_bugs_by_bug(test_bugs, output_path: Path):
    labels = []

    for bug in test_bugs:
        if not bug.relation or not bug.relation.regressions:
            continue

        print("\n" + "=" * 80)
        print("Test Bug / PR:")
        print(bug)
        print("=" * 80)

        for introduced_bug_id in bug.relation.regressions:
            print("\n" + "-" * 60)
            print(f"Introduced Bug ID: {introduced_bug_id}")
            print("Please open the bug link and inspect it manually.")

            detected_by_us = choose_detected_by_us()
            bug_type = choose_introduced_bug_type()
            bug_status = choose_bug_status()
            note = input("Optional note (press Enter to skip): ").strip()

            labels.append(
                IntroducedBugLabel(
                    parent_bug_id=int(bug.id),
                    introduced_bug_id=int(introduced_bug_id),
                    bug_type=bug_type.value,
                    bug_status=bug_status,
                    detected_by_us=detected_by_us,
                    note=note
                )
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(l) for l in labels], f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved introduced bug labels to {output_path}")


# ===================== Entry =====================

if __name__ == "__main__":

    reponame = APP_NAME_FIREFOX
    test_bugs_foldername = "test_bugs"

    test_bugs_path = Path(DATA_DIR, reponame, test_bugs_foldername)
    test_bugs = FileUtil.load_pickle(
        Path(test_bugs_path, f"{test_bugs_foldername}.json")
    )

    output_file = Path(
        OUTPUT_DIR, reponame, "introduced_bug_labels.json"
    )

    label_introduced_bugs_by_bug(test_bugs, output_file)
