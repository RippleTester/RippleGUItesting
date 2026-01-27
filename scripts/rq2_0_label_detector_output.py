import json
from enum import Enum
from pathlib import Path

from src.pipelines.placeholder import Placeholder
from src.pipelines.post_processor import PostProcessor
from src.utils.file_util import FileUtil
from config import DATA_DIR, APP_NAME_FIREFOX, OUTPUT_DIR, APP_NAME_ZETTLR, APP_NAME_JABREF, APP_NAME_GODOT
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# ========== 数据结构定义 ==========

class DetectorFalsePositiveReason(Enum):
    """Enumerates common causes for false positive detections in detector."""
    SCREENSHOT_TIMING = "Screenshot timing or rendering delay"
    HALLUCINATED_ACTION = "LLM hallucination — predicted an non-executed action as executed"
    HALLUCINATED_RENDERING = "LLM hallucination — misinterpreted or imagined GUI rendering"
    VERSION_DIFF = "Firefox version differences, possibly involving multiple code changes"
    ELEMENT_LOCATION_ERROR = "GUI element location or interaction error (non-deterministic behavior)"
    UNNECESSARY_SUGGESTION = "Unreasonable or unnecessary improvement suggestion, not a real issue"
    LAYOUT_SHIFT_CLICK = "UI layout shift leading to incorrect replay click"
    UNCERTAIN_CLASSIFICATION = "Uncertain whether true positive or false positive"
    EXPECTED_CHANGE = "Expected GUI difference due to intended code change"
    CODE_INDUCED_GUI_DIFF = "Code-induced GUI difference leading to replay mismatch"
    UNSTABLE_TEST_DATA = "Unstable test data causing GUI inconsistency during replay"
    UNSTABLE_GUI_LAYOUT = "Unstable GUI layout/rendering"
    OTHER = "Other"

@dataclass
class DiscoveredBug:
    bug_report: str
    is_duplicate: bool
    is_true_positive: Optional[bool] = None
    is_introduced: Optional[bool] = None
    hit_ground_truth: Optional[Enum] = None
    false_positive_reasons: List[DetectorFalsePositiveReason] = field(default_factory=list)

class DetectorMissedReason(Enum):
    """Reasons why a revealed bug was not detected by the detector."""
    OVERLOOKED_BEHAVIOR = "LLM overlooking the buggy behavior"
    HALLUCINATION = "LLM hallucination"
    OTHER = "Other"

@dataclass
class UndiscoveredBug:
    description: str
    is_duplicate: bool
    is_introduced: Optional[bool] = None
    hit_ground_truth: Optional[Enum] = None
    missed_reasons: List[DetectorMissedReason] = field(default_factory=list)


@dataclass
class TestScenario:
    scenario_no: int
    discovered_bugs: List[DiscoveredBug] = field(default_factory=list)
    undiscovered_but_revealed_bugs: List[UndiscoveredBug] = field(default_factory=list)


@dataclass
class TestBug:
    bug_id: int
    ground_truth_bug_ids: List[int]
    test_scenarios: List[TestScenario] = field(default_factory=list)

# ======== Helper Functions ========
def choose_from_enum(enum_cls: Enum) -> List[Enum | str]:
    """Let user choose one or more enum values, allowing custom input for 'Other'."""
    print("\nSelect reason(s) (comma-separated numbers):")
    for i, e in enumerate(enum_cls, start=1):
        print(f"{i}. {e.value}")
    sel = input("Your choice(s): ").strip()

    # Parse indices
    indices = [int(x) for x in sel.split(",") if x.strip().isdigit()]
    chosen = [list(enum_cls)[i - 1] for i in indices if 1 <= i <= len(enum_cls)]

    # Default to OTHER if nothing selected
    if not chosen:
        print("No selection — defaulting to OTHER.")
        chosen = [list(enum_cls)[-1]]

    # If OTHER selected, ask for details
    result = []
    for item in chosen:
        if item == list(enum_cls)[-1]:  # The "Other" enum value
            custom_reason = input("Please specify the custom reason for 'Other': ").strip()
            result.append(custom_reason or "Other (unspecified)")
        else:
            result.append(item)

    return result

def choose_from_ground_truth(ground_truth_ids: List[int]) -> Optional[int]:
    """Let user pick which ground truth bug was hit (or None)."""
    print("\nSelect hit ground truth (enter number):")
    for i, gid in enumerate(ground_truth_ids, start=1):
        print(f"{i}. {gid}")
    print(f"{len(ground_truth_ids) + 1}. None")
    choice = input("Your choice: ").strip()
    if not choice.isdigit():
        return None
    index = int(choice)
    return None if index > len(ground_truth_ids) else ground_truth_ids[index - 1]


def label_discovered_bug(bug_report: str, ground_truth_ids: List[int]) -> DiscoveredBug:
    """Label a discovered bug interactively."""
    print("\n=== Label Discovered Bug ===")
    print(f"Bug Report:\n{bug_report}\n")

    is_duplicate = input("Is this a duplicate? (y/n): ").lower() == "y"
    if is_duplicate:
        return DiscoveredBug(bug_report=bug_report, is_duplicate=True)

    is_true_positive = input("Is this a true positive? (y/n): ").lower() == "y"
    if is_true_positive:
        is_introduced = input("Was it introduced by this code change? (y/n): ").lower() == "y"
        hit_gt = None
        if is_introduced:
            hit_gt = choose_from_ground_truth(ground_truth_ids)
        return DiscoveredBug(
            bug_report=bug_report,
            is_duplicate=False,
            is_true_positive=True,
            is_introduced=is_introduced,
            hit_ground_truth=hit_gt,
        )
    else:
        reasons = choose_from_enum(DetectorFalsePositiveReason)
        return DiscoveredBug(
            bug_report=bug_report,
            is_duplicate=False,
            is_true_positive=False,
            false_positive_reasons=reasons
        )


def parse_detector_output(detector_output, post_processor_output=None, bug_index=None) -> List[str]:
    """Extract discovered bug report strings from detector output."""
    discovered = []
    for idx, entry in enumerate(detector_output):
        if idx % 2 == 1:  # odd indices contain detected bugs
            for report in entry["bug_reports"]:
                if post_processor_output["bug_report_flags"][bug_index]["keep"]:
                    discovered.append(report)
                bug_index = bug_index + 1

    print(f"🪲 Extracted {len(discovered)} discovered bug reports")
    return discovered, bug_index

def label_undiscovered_bug(ground_truth_ids: List[int]) -> UndiscoveredBug:
    """Label a revealed but undiscovered bug."""
    print("\n=== Label Undiscovered Bug ===")
    description = input("Bug description: ").strip()
    is_duplicate = input("Is this a duplicate? (y/n): ").lower() == "y"
    if is_duplicate:
        return UndiscoveredBug(description=description, is_duplicate=True)

    is_introduced = input("Was it introduced by this code change? (y/n): ").lower() == "y"
    hit_gt = None
    if is_introduced:
        hit_gt = choose_from_ground_truth(ground_truth_ids)
    reasons = choose_from_enum(DetectorMissedReason)
    return UndiscoveredBug(
        description=description,
        is_duplicate=False,
        is_introduced=is_introduced,
        hit_ground_truth=hit_gt,
        missed_reasons=reasons
    )


def label_test_scenario(scenario_no: int, ground_truth_ids: List[int]) -> TestScenario:
    """Label all bugs in a test scenario."""
    print(f"\n=== Label Test Scenario #{scenario_no} ===")
    discovered = []
    undiscovered = []

    num_discovered = int(input("How many discovered bugs? "))
    for _ in range(num_discovered):
        discovered.append(label_discovered_bug(ground_truth_ids))

    num_undiscovered = int(input("How many undiscovered but revealed bugs? "))
    for _ in range(num_undiscovered):
        undiscovered.append(label_undiscovered_bug(ground_truth_ids))

    return TestScenario(
        scenario_no=scenario_no,
        discovered_bugs=discovered,
        undiscovered_but_revealed_bugs=undiscovered
    )


def save_labels(bug: TestBug, output_dir: Path):
    """Save labeled data as JSON."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = Path(output_dir, f"{bug.bug_id}_detector_labels.json")

    data = asdict(bug)
    # Convert Enums to string values for JSON serialization
    def enum_to_value(obj):
        if isinstance(obj, list):
            return [enum_to_value(o) for o in obj]
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, dict):
            return {k: enum_to_value(v) for k, v in obj.items()}
        return obj
    data = enum_to_value(data)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved labels to {output_file}")


if __name__ == "__main__":
    # @todo uncovered bugs? <- image diff replayer.json parsed_info
    """
    TestBug/code change
     ├─ ground_truth_bugs (list of Bug IDs)
     ├─ test_scenarios (list of TestScenario)
     │     ├─ discovered_bugs (list of DiscoveredBug)
     │     │     ├─ is_duplicate (bool)
     │     │     │     └─ if True → quit
     │     │     ├─ is_true_positive (bool)
     │     │     │     ├─ if True:
     │     │     │     │     └─ is_introduced (bool)
     │     │     │     │          ├─ True → hit_ground_truth (ground_truth_bug ids as options and a none option)
     │     │     │     │          └─ False → (A real bug but not introduced by this code change)
     │     │     │     └─ if False:
     │     │     │           └─ false_positive_reasons (enum)
     │     ├─ undiscovered_but_revealed_bugs (list of UndiscoveredBug)
     │     │     ├─ is_duplicate (bool)
     │     │     │     └─ if True → quit
     │     │     ├─ is_introduced (bool)
     │     │     │     ├─ True → hit_ground_truth (ground_truth_bug ids as options and a none option)
     │     │     │     └─ False
     │     │     └─ missed_reasons (enum)
    """
    reponame = APP_NAME_FIREFOX
    # reponame = APP_NAME_ZETTLR
    # reponame = APP_NAME_JABREF
    # reponame = APP_NAME_GODOT
    if reponame == APP_NAME_FIREFOX:
        test_bugs_foldername = "test_bugs"
        test_bugs_filename = "test_bugs"
    else:
        test_bugs_foldername = "test_pulls"
        test_bugs_filename = "selected_test_pulls"
    test_bugs_filepath = Path(DATA_DIR, reponame, f'{test_bugs_foldername}')
    output_filepath = Path(OUTPUT_DIR, reponame, 'output')
    detector_output_evaluation_filepath = Path(OUTPUT_DIR, reponame, 'detector_output_evaluation')
    test_bugs = FileUtil.load_pickle(Path(test_bugs_filepath, f'{test_bugs_filename}.json'))
    test_bugs = sorted(test_bugs, key=lambda bug: bug.id, reverse=True)
    # for bug in test_bugs:
    #     print(bug.id)
    # print(len(test_bugs))
    for bug in test_bugs[21:]:
        if bug:
            bug_id = bug.id
            if reponame != APP_NAME_FIREFOX:
                bug_id = bug.extract_number_from_github_url()
            bug_id = str(bug_id)
            print(f"{bug} ###########################################################")
            bug_dir = Path(output_filepath, bug_id)
            # First-level directories
            first_level_dir = [d for d in bug_dir.iterdir() if d.is_dir()][0]
            # Second-level directories (e.g., numbered scenario folders)
            second_level_dirs = [d for d in first_level_dir.iterdir() if d.is_dir()]
            second_level_dirs.sort()
            print(f"Test Scenarios Num: {len(second_level_dirs)}")
            bug_index = 0
            post_processor_output = FileUtil.load_json(Path(first_level_dir,
                                                            f"{Placeholder.POST_PROCESSOR}.json"))
            test_scenarios = []
            ground_truth_ids = []
            for i, subdir in enumerate(second_level_dirs):
                print(f"No. Test Scenario: {subdir.name} *******************************")
                # Search for detector*.json files
                detector_file = list(subdir.glob("detector*.json"))[0]
                detector_output = FileUtil.load_json(detector_file)
                # Extract discovered bugs automatically
                discovered_reports, bug_index = parse_detector_output(detector_output,
                                                                      post_processor_output, bug_index)
                if len(discovered_reports) > 0:
                    # Search for output.pdf file
                    pdf_file = subdir / "output.pdf"
                    FileUtil.open_file(pdf_file)

                discovered_bugs = []
                if bug.relation and bug.relation.regressions:
                    ground_truth_ids = bug.relation.regressions
                for report in discovered_reports:
                    discovered_bugs.append(label_discovered_bug(report, ground_truth_ids=ground_truth_ids))

                scenario = TestScenario(
                    scenario_no=i,
                    discovered_bugs=discovered_bugs,
                )
                test_scenarios.append(scenario)
            labeled_bug = TestBug(
                bug_id=int(bug_id),
                ground_truth_bug_ids=ground_truth_ids,
                test_scenarios=test_scenarios
            )
            save_labels(labeled_bug, detector_output_evaluation_filepath)
            print("\n✅ Finished labeling for this TestBug.")
            input("Press Enter to continue to the next one...")