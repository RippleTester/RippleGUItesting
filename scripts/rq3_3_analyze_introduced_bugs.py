import json
from pathlib import Path
from collections import Counter, defaultdict

from config import OUTPUT_DIR, APP_NAME_FIREFOX


LOG_BUG_TYPE = "Crash / stack trace / error log"


def analyze_introduced_bug_labels(label_file: Path):
    with open(label_file, "r", encoding="utf-8") as f:
        labels = json.load(f)

    type_counter = Counter()
    status_counter = Counter()
    detected_counter = Counter()

    type_detected = defaultdict(Counter)
    status_detected = defaultdict(Counter)

    log_bug_count = 0
    log_status_counter = Counter()

    for item in labels:
        bug_type = item.get("bug_type", "Unknown")
        bug_status = item.get("bug_status", "Unknown")
        detected = item.get("detected_by_us", False)

        detected_str = "Detected" if detected else "Not detected"

        type_counter[bug_type] += 1
        status_counter[bug_status] += 1
        detected_counter[detected_str] += 1

        type_detected[bug_type][detected_str] += 1
        status_detected[bug_status][detected_str] += 1

        if bug_type == LOG_BUG_TYPE:
            log_bug_count += 1
            log_status_counter[bug_status] += 1

    return (
        type_counter,
        status_counter,
        detected_counter,
        type_detected,
        status_detected,
        log_bug_count,
        log_status_counter
    )


def print_counter(title, counter: Counter):
    print(f"\n=== {title} ===")
    total = sum(counter.values())
    for k, v in counter.most_common():
        print(f"{k}: {v} ({v / total:.1%})")
    print(f"Total: {total}")


def print_cross(title, cross_dict):
    print(f"\n=== {title} ===")
    for key, sub in cross_dict.items():
        total = sum(sub.values())
        print(f"\n{key} (Total: {total})")
        for k, v in sub.items():
            print(f"  {k}: {v} ({v / total:.1%})")


def print_log_bug_stats(total, counter: Counter):
    print("\n=== Crash / Log Bugs Summary ===")
    print(f"Total Crash / Log Bugs: {total}")

    if total == 0:
        print("No Crash / Log bugs found.")
        return

    print("\n--- Crash / Log Bugs × Bug Status ---")
    for status, count in counter.most_common():
        print(f"{status}: {count} ({count / total:.1%})")


# ===================== Entry =====================

if __name__ == "__main__":
    reponame = APP_NAME_FIREFOX

    label_file = Path(
        OUTPUT_DIR, reponame, "introduced_bug_labels.json"
    )

    (
        type_counter,
        status_counter,
        detected_counter,
        type_detected,
        status_detected,
        log_bug_count,
        log_status_counter
    ) = analyze_introduced_bug_labels(label_file)

    print_counter("Introduced Bug Type Distribution", type_counter)
    print_counter("Bug Status Distribution", status_counter)
    print_counter("Detected by Our Approach", detected_counter)

    print_cross("Bug Type × Detected", type_detected)
    print_cross("Bug Status × Detected", status_detected)

    print_log_bug_stats(log_bug_count, log_status_counter)
