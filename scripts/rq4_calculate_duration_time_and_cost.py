from pathlib import Path


from config import (
    APP_NAME_ZETTLR,
    OUTPUT_DIR,
    APP_NAME_JABREF,
    APP_NAME_FIREFOX,
    APP_NAME_GODOT,
)
from src.pipelines.placeholder import Placeholder
from src.utils.file_util import FileUtil

if __name__ == "__main__":
    # reponame = APP_NAME_FIREFOX
    # reponame = APP_NAME_ZETTLR
    reponame = APP_NAME_GODOT
    # reponame = APP_NAME_JABREF

    output_filepath = Path(OUTPUT_DIR, reponame, "output")

    numeric_folders = [
        p for p in output_filepath.iterdir()
        if p.is_dir() and p.name[0].isdigit()
    ]
    total_pr_num = len(numeric_folders)

    # ===================== Accumulators =====================

    # Overall
    total_duration = 0.0
    total_cost = 0.0

    # Test scenario generation
    gen_duration = 0.0
    gen_cost = 0.0

    # Test scenario execution
    exec_duration = 0.0
    exec_cost = 0.0

    # Bug detection
    detect_duration = 0.0
    detect_cost = 0.0

    # ===================== Traversal =====================

    for pr_folder in numeric_folders:

        # ---------- Test Scenario Generation ----------
        for name in ["generator.json", "data_enhancer.json", "path_enhancer.json"]:
            for path in pr_folder.rglob(name):
                output = FileUtil.load_json(path)

                duration = output[2]["content"][Placeholder.DURATION_MINS]
                cost = output[2]["content"][Placeholder.COST][Placeholder.TOTAL_COST]

                gen_duration += duration
                gen_cost += cost
                total_duration += duration
                total_cost += cost

        # ---------- Execution & Detection ----------
        for folder in pr_folder.rglob("*"):
            if not (folder.is_dir() and folder.name[0].isdigit()):
                continue

            # Execution
            replayer = folder / "replayer.json"
            if replayer.exists():
                output = FileUtil.load_json(replayer)

                duration = output[Placeholder.DURATION_MINS]
                cost = output[Placeholder.TOTAL_COST]

                exec_duration += duration
                exec_cost += cost
                total_duration += duration
                total_cost += cost

            # Detection
            for detector in folder.glob("detector_*.json"):
                output = FileUtil.load_json(detector)
                if not output:
                    continue

                duration = output[-1][Placeholder.TOTAL_DURATION_MINS]
                cost = output[-1][Placeholder.TOTAL_COST]

                detect_duration += duration
                detect_cost += cost
                total_duration += duration
                total_cost += cost
        # ---------- Post-processing (belongs to Detection) ----------
        for path in pr_folder.rglob("post_processor.json"):
            output = FileUtil.load_json(path)

            duration = output[Placeholder.DURATION_MINS]
            cost = output[Placeholder.COST][Placeholder.TOTAL_COST]

            detect_duration += duration
            detect_cost += cost
            total_duration += duration
            total_cost += cost


    # ===================== Reporting =====================

    def avg(x):
        return x / total_pr_num if total_pr_num > 0 else 0.0

    def pct(x, total):
        return (x / total * 100.0) if total > 0 else 0.0

    print("=" * 72)
    print(f"Repository: {reponame}")
    print(f"Total PR number: {total_pr_num}")
    print("-" * 72)

    print("[Test Scenario Generation]")
    print(f"  Time: {gen_duration:.2f} mins "
          f"({pct(gen_duration, total_duration):.1f}% of total time)")
    print(f"  Cost: ${gen_cost:.2f} "
          f"({pct(gen_cost, total_cost):.1f}% of total cost)")
    print(f"  Avg time / PR: {avg(gen_duration):.2f} mins")
    print(f"  Avg cost / PR: ${avg(gen_cost):.2f}")
    print()

    print("[Test Scenario Execution]")
    print(f"  Time: {exec_duration:.2f} mins "
          f"({pct(exec_duration, total_duration):.1f}% of total time)")
    print(f"  Cost: ${exec_cost:.2f} "
          f"({pct(exec_cost, total_cost):.1f}% of total cost)")
    print(f"  Avg time / PR: {avg(exec_duration):.2f} mins")
    print(f"  Avg cost / PR: ${avg(exec_cost):.2f}")
    print()

    print("[Bug Detection]")
    print(f"  Time: {detect_duration:.2f} mins "
          f"({pct(detect_duration, total_duration):.1f}% of total time)")
    print(f"  Cost: ${detect_cost:.2f} "
          f"({pct(detect_cost, total_cost):.1f}% of total cost)")
    print(f"  Avg time / PR: {avg(detect_duration):.2f} mins")
    print(f"  Avg cost / PR: ${avg(detect_cost):.2f}")
    print()

    print("[Overall]")
    print(f"  Time: {total_duration:.2f} mins (100.0%)")
    print(f"  Cost: ${total_cost:.2f} (100.0%)")
    print(f"  Avg time / PR: {avg(total_duration):.2f} mins")
    print(f"  Avg cost / PR: ${avg(total_cost):.2f}")
    print("=" * 72)
