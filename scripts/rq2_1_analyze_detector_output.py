import json
from pathlib import Path
from statistics import mean
from collections import Counter

from config import OUTPUT_DIR, APP_NAME_FIREFOX, APP_NAME_ZETTLR, APP_NAME_JABREF, APP_NAME_GODOT


def analyze_test_bugs_basic_info(reponame):
    # reponame = APP_NAME_FIREFOX
    labels_dir = Path(OUTPUT_DIR, reponame, "detector_output_evaluation")

    # Find all labeled json files
    label_files = sorted(labels_dir.glob("*_detector_labels.json"))
    if not label_files:
        print("⚠️ No labeled JSON files found.")
        return

    summary = []

    for file in label_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        bug_id = data.get("bug_id")
        gt_bugs = data.get("ground_truth_bug_ids", [])
        test_scenarios = data.get("test_scenarios", [])

        summary.append({
            "bug_id": bug_id,
            "ground_truth_count": len(gt_bugs),
            "test_scenario_count": len(test_scenarios)
        })

    # === Compute statistics ===
    total_bugs = len(summary)
    avg_gt = mean([s["ground_truth_count"] for s in summary]) if summary else 0
    avg_scenarios = mean([s["test_scenario_count"] for s in summary]) if summary else 0

    # === Print report ===
    print("\n" + "="*60)
    print("📊 Labeling Summary")
    print("-"*60)
    print(f"Total TestBugs labeled: {total_bugs}")
    print(f"Average number of ground truth bugs per TestBug: {avg_gt:.2f}")
    print(f"Average number of test scenarios per TestBug: {avg_scenarios:.2f}\n")

def analyze_detector_results(detector_results):
    total_detected_bugs = 0
    true_positives = 0
    true_positives_introduced = 0
    true_positives_introduced_groundtruth = 0
    false_positives = 0
    # detected_detected_bugs_per_test_bug = 0
    for result in detector_results:
        for test_scenario in result["test_scenarios"]:
            if test_scenario['discovered_bugs']:
                for discovered_bug in test_scenario['discovered_bugs']:
                    if not discovered_bug['is_duplicate']:
                        total_detected_bugs += 1
                        if discovered_bug['is_true_positive']:
                            true_positives += 1
                            if discovered_bug['is_true_positive'] and discovered_bug['is_introduced']:
                                true_positives_introduced += 1
                                if discovered_bug['hit_ground_truth']:
                                    true_positives_introduced_groundtruth += 1
                        else:
                            false_positives += 1
    print(f"Total detected bugs: {total_detected_bugs}")
    print(f"total detected bugs per test bug: {total_detected_bugs / len(detector_results)}")
    print("*************************")
    print(f"true positives: {true_positives}")
    print(f"true positive ratio: {true_positives/total_detected_bugs}")
    print(f"true positive introduced: {true_positives_introduced}")
    print(f"true positive introduced groundtruth: {true_positives_introduced_groundtruth}")
    print("*************************")
    print(f"false positives: {false_positives}")
    print(f"false positive ratio: {false_positives/total_detected_bugs}")
    print("*************************")


def analyze_false_positive_reasons(detector_results):
    """统计所有 False Positive 的原因分布。"""
    counter = Counter()
    total_fp = 0

    for result in detector_results:
        for test_scenario in result["test_scenarios"]:
            for discovered_bug in test_scenario.get("discovered_bugs", []):
                # 跳过重复项
                if discovered_bug.get("is_duplicate", False):
                    continue
                # 只统计 False Positive
                if discovered_bug.get("is_true_positive") is False:
                    total_fp += 1
                    reasons = discovered_bug.get("false_positive_reasons", [])
                    # 每个 bug 可能有多个原因
                    for r in reasons:
                        if isinstance(r, dict):
                            r = r.get("value", "Other")
                        elif not isinstance(r, str):
                            r = str(r)
                        counter[r] += 1

    print("\n" + "=" * 60)
    print("📊 False Positive Reason Statistics")
    print("-" * 60)
    print(f"Total false positives: {total_fp}")
    print(f"Unique reason categories: {len(counter)}\n")

    total_reasons = sum(counter.values())
    if total_reasons == 0:
        print("⚠️ No false positive reasons found.")
        return

    # 输出按出现频次排序的统计
    for reason, count in counter.most_common():
        ratio = count / total_reasons * 100
        print(f"{reason:<65} {count:>4} ({ratio:5.2f}%)")

    print("=" * 60)

def calculate_hit_groundtruth_rate(detector_results):
    hit_rate = 0
    for result in detector_results:
        hit_flag = False
        for test_scenario in result["test_scenarios"]:
            if test_scenario['discovered_bugs']:
                for discovered_bug in test_scenario['discovered_bugs']:
                    if discovered_bug['hit_ground_truth']:
                        hit_rate += 1
                        hit_flag = True
                        # print(result["bug_id"])
                        break
                if hit_flag:
                    break
    hit_rate = hit_rate / len(detector_results)
    print(f"ground truth hit rate: {hit_rate:.2f}")

def calculate_hit_rate(detector_results):
    hit_rate = 0
    for result in detector_results:
        hit_flag = False
        for test_scenario in result["test_scenarios"]:
            if test_scenario['discovered_bugs']:
                for discovered_bug in test_scenario['discovered_bugs']:
                    if discovered_bug['is_introduced']:
                        hit_rate += 1
                        hit_flag = True
                        # print(result["bug_id"])
                        break
                if hit_flag:
                    break
    hit_rate = hit_rate / len(detector_results)
    print(f"hit rate: {hit_rate:.2f}")

def analyze_detector_performance(reponame):
    # reponame = APP_NAME_FIREFOX
    labels_dir = Path(OUTPUT_DIR, reponame, "detector_output_evaluation")

    json_files = sorted(labels_dir.glob("*_detector_labels.json"))
    if not json_files:
        print("⚠️ No labeled JSON files found.")
        return
    detector_results = []

    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            data = json.load(f)
            detector_results.append(data)
    analyze_detector_results(detector_results)
    analyze_false_positive_reasons(detector_results)   # 👈 新增这一行

    calculate_hit_groundtruth_rate(detector_results)
    calculate_hit_rate(detector_results)

if __name__ == "__main__":
    reponame = APP_NAME_ZETTLR
    # reponame = APP_NAME_JABREF
    # reponame = APP_NAME_GODOT
    # reponame = APP_NAME_FIREFOX
    analyze_test_bugs_basic_info(reponame)
    analyze_detector_performance(reponame)
